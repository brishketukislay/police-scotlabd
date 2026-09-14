from __future__ import annotations

import math
from typing import Iterable, TypedDict


class Point(TypedDict):
    x: float
    y: float


SUPPORTED_SHAPES = {"circle", "square", "triangle"}


def _distance(a: Point, b: Point) -> float:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def _dedupe(points: Iterable[Point]) -> list[Point]:
    result: list[Point] = []

    for point in points:
        p = {"x": float(point["x"]), "y": float(point["y"])}

        if not result or _distance(result[-1], p) > 0.002:
            result.append(p)

    return result


def _path_length(points: list[Point]) -> float:
    return sum(
        _distance(points[index - 1], points[index])
        for index in range(1, len(points))
    )


def _resample(points: list[Point], count: int = 64) -> list[Point]:
    if len(points) < 2:
        return points

    total = _path_length(points)

    if total <= 0:
        return [points[0]] * count

    interval = total / (count - 1)
    result = [points[0]]

    accumulated = 0.0
    previous = points[0]
    index = 1

    while index < len(points):
        current = points[index]
        segment = _distance(previous, current)

        if accumulated + segment >= interval:
            ratio = (
                (interval - accumulated) / segment
                if segment > 0
                else 0
            )

            inserted = {
                "x": previous["x"]
                + ratio * (current["x"] - previous["x"]),
                "y": previous["y"]
                + ratio * (current["y"] - previous["y"]),
            }

            result.append(inserted)
            previous = inserted
            accumulated = 0.0
        else:
            accumulated += segment
            previous = current
            index += 1

    while len(result) < count:
        result.append(points[-1])

    return result[:count]


def _normalise(points: list[Point]) -> list[Point]:
    min_x = min(p["x"] for p in points)
    max_x = max(p["x"] for p in points)
    min_y = min(p["y"] for p in points)
    max_y = max(p["y"] for p in points)

    width = max(max_x - min_x, 1e-6)
    height = max(max_y - min_y, 1e-6)

    scale = max(width, height)

    return [
        {
            "x": (p["x"] - min_x) / scale,
            "y": (p["y"] - min_y) / scale,
        }
        for p in points
    ]


def target_points(shape: str, count: int = 64) -> list[Point]:
    if shape not in SUPPORTED_SHAPES:
        raise ValueError(f"Unsupported shape: {shape}")

    if shape == "circle":
        return [
            {
                "x": 0.5 + 0.38 * math.cos(
                    (2 * math.pi * i) / (count - 1)
                ),
                "y": 0.5 + 0.38 * math.sin(
                    (2 * math.pi * i) / (count - 1)
                ),
            }
            for i in range(count)
        ]

    if shape == "square":
        vertices = [
            {"x": 0.15, "y": 0.15},
            {"x": 0.85, "y": 0.15},
            {"x": 0.85, "y": 0.85},
            {"x": 0.15, "y": 0.85},
            {"x": 0.15, "y": 0.15},
        ]
    else:
        vertices = [
            {"x": 0.5, "y": 0.12},
            {"x": 0.88, "y": 0.82},
            {"x": 0.12, "y": 0.82},
            {"x": 0.5, "y": 0.12},
        ]

    result: list[Point] = []

    segment_lengths = [
        _distance(vertices[i], vertices[i + 1])
        for i in range(len(vertices) - 1)
    ]
    total = sum(segment_lengths)

    for i in range(count):
        wanted = (i / (count - 1)) * total
        travelled = 0.0

        for segment_index, segment_length in enumerate(segment_lengths):
            if travelled + segment_length >= wanted:
                ratio = (
                    (wanted - travelled) / segment_length
                    if segment_length
                    else 0
                )
                start = vertices[segment_index]
                end = vertices[segment_index + 1]

                result.append(
                    {
                        "x": start["x"]
                        + ratio * (end["x"] - start["x"]),
                        "y": start["y"]
                        + ratio * (end["y"] - start["y"]),
                    }
                )
                break

            travelled += segment_length

    return result


def calculate_accuracy(
    shape: str,
    user_points: list[Point],
) -> float:
    """
    Returns a deterministic 0..100 accuracy score.

    The browser never sends the score or XP. It only sends stroke points.
    """

    if shape not in SUPPORTED_SHAPES:
        raise ValueError(f"Unsupported shape: {shape}")

    points = _dedupe(user_points)

    if len(points) < 8:
        return 0.0

    user = _resample(points)
    target = target_points(shape)

    user = _normalise(user)
    target = _normalise(target)

    average_error = sum(
        _distance(user[i], target[i])
        for i in range(len(target))
    ) / len(target)

    # 0.35 is deliberately generous for a youth-facing mini-game.
    geometry_score = max(
        0.0,
        min(100.0, (1.0 - average_error / 0.35) * 100.0),
    )

    closure_error = _distance(user[0], user[-1])
    closure_score = max(
        0.0,
        min(100.0, (1.0 - closure_error / 0.5) * 100.0),
    )

    # A player should actually trace most of the shape.
    drawn_length = _path_length(user)
    target_length = _path_length(target)

    coverage = (
        min(drawn_length / target_length, 1.0)
        if target_length > 0
        else 0.0
    )
    coverage_score = coverage * 100.0

    # Geometry is dominant; closure and coverage prevent trivial strokes
    # from receiving high scores.
    score = (
        geometry_score * 0.70
        + closure_score * 0.15
        + coverage_score * 0.15
    )

    return round(max(0.0, min(100.0, score)), 2)


def resolve_xp(
    accuracy: float,
    brackets: list[dict[str, int]],
) -> int:
    for bracket in brackets:
        if (
            bracket["min"]
            <= accuracy
            <= bracket["max"]
        ):
            return int(bracket["xp"])

    return 0
