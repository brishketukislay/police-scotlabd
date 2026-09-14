from datetime import datetime, timedelta

from app.db.database import SessionLocal
from app.db.models import Challenge, Phase, Programme


db = SessionLocal()

try:
    programme = (
        db.query(Programme)
        .filter(Programme.active.is_(True))
        .first()
    )

    if programme is None:
        raise SystemExit(
            "No active programme found. Run seed.py first."
        )

    existing = (
        db.query(Challenge)
        .filter(
            Challenge.programme_id == programme.id,
            Challenge.title == "Community Spotter",
        )
        .first()
    )

    if existing:
        print(
            f"Challenge already exists: "
            f"#{existing.id} {existing.title}"
        )
    else:
        phase = (
            db.query(Phase)
            .filter(
                Phase.programme_id == programme.id,
                Phase.active.is_(True),
            )
            .order_by(Phase.sort_order.asc())
            .first()
        )

        now = datetime.utcnow()

        challenge = Challenge(
            programme_id=programme.id,
            phase_id=phase.id if phase else None,
            title="Community Spotter",
            description=(
                "Take part in the Community Spotter challenge. "
                "Complete the activity and submit your result."
            ),
            game_type="generic",
            config_json=(
                '{"minimum_score":0,'
                '"elite_percentile":90}'
            ),
            start_at=now - timedelta(minutes=5),
            end_at=now + timedelta(days=30),
            participation_xp=300,
            elite_xp=1500,
            winner_xp=3000,
            group_xp=5000,
            active=True,
        )

        db.add(challenge)
        db.commit()
        db.refresh(challenge)

        print(
            f"Created challenge: "
            f"#{challenge.id} {challenge.title}"
        )

finally:
    db.close()
