from __future__ import annotations

from sqlalchemy.orm import Session

from ..db.models import Player, Reward, PlayerReward


def grant_eligible_rewards(
    db: Session,
    *,
    player: Player,
    lifetime_xp: int,
) -> list[PlayerReward]:
    """
    Grant every active reward whose XP threshold has been reached.

    This function does not commit.

    Reward definitions live in Reward.
    Actual player awards live in PlayerReward.

    The operation is idempotent: calling this repeatedly will not
    create duplicate PlayerReward records for the same player/reward.
    """

    rewards = (
        db.query(Reward)
        .filter(
            Reward.programme_id == player.programme_id,
            Reward.active.is_(True),
        )
        .order_by(
            Reward.xp_threshold.asc(),
            Reward.id.asc(),
        )
        .all()
    )

    existing_reward_ids = {
        player_reward.reward_id
        for player_reward in (
            db.query(PlayerReward)
            .filter(
                PlayerReward.player_id == player.id,
            )
            .all()
        )
    }

    granted: list[PlayerReward] = []

    for reward in rewards:
        if reward.xp_threshold is None:
            continue

        if lifetime_xp < reward.xp_threshold:
            continue

        if reward.id in existing_reward_ids:
            continue

        player_reward = PlayerReward(
            player_id=player.id,
            reward_id=reward.id,
            status="pending",
        )

        db.add(player_reward)
        db.flush()

        existing_reward_ids.add(reward.id)
        granted.append(player_reward)

    return granted
