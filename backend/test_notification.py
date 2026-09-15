#!/usr/bin/env python3
"""
End-to-end test for notification creation when awarding XP.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Programme, Player
from app.services.xp import award_xp

def test_notification_on_xp_award() -> None:
    # Use a context manager for the session
    db: Session = SessionLocal()
    try:
        # Start a transaction and rollback at the end to avoid polluting the database
        with db.begin():
            # Find an existing programme and player to use
            programme = db.query(Programme).first()
            if not programme:
                print("ERROR: No programme found in database")
                return
            player = db.query(Player).first()
            if not player:
                print("ERROR: No player found in database")
                return

            print(f"Using programme ID: {programme.id}, player ID: {player.id}")

            # Call award_xp with a test reference
            reference_type = "test_ref"
            reference_id = 999
            transaction = award_xp(
                db,
                programme_id=programme.id,
                player_id=player.id,
                amount=10,
                group_amount=0,
                transaction_type="test",
                reason="Test notification creation",
                reference_type=reference_type,
                reference_id=reference_id,
                idempotency_key=f"test-notif-{reference_type}-{reference_id}",
            )
            print(f"Created XP transaction ID: {transaction.id}")

            # Query for a notification with the same reference
            from app.db.models import Notification
            notification = (
                db.query(Notification)
                .filter(
                    Notification.reference_type == reference_type,
                    Notification.reference_id == reference_id,
                )
                .first()
            )

            if notification:
                print(f"SUCCESS: Found notification ID: {notification.id}")
                print(f"  Notification title: {notification.title}")
                print(f"  Notification body: {notification.body}")
                print(f"  Notification type: {notification.notification_type}")
                print(f"  Active: {notification.active}")
            else:
                print("ERROR: No notification found with the given reference")
                # Print all notifications for debugging
                all_notifs = db.query(Notification).all()
                print(f"Total notifications in DB: {len(all_notifs)}")
                for n in all_notifs[:5]:  # Show first 5
                    print(f"  ID: {n.id}, ref: {n.reference_type}:{n.reference_id}")

    except Exception as e:
        print(f"ERROR during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_notification_on_xp_award()