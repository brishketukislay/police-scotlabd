from datetime import date

from app.db.base import Base
from app.db.database import SessionLocal, init_db
from app.db.models import (
    User,
    Programme,
    Theme,
    GameMap,
    MapLocation,
    Phase,
    YouthGroup,
    Player,
    PointRule,
    SkillTree,
    SkillMilestone,
)
from app.auth import hash_password

# The seed script must also bootstrap a fresh database.  The application
# normally creates tables during startup, but `seed.py` is documented as
# the first backend command to run.

init_db()

db = SessionLocal()

if db.query(User).count() == 0:
    theme = Theme(
        name="Forest",
        primary="#18775B",
        secondary="#0F513C",
        accent="#43B98B",
        background="#F3F7F5",
        surface="#FFFFFF",
        text="#17221E",
    )
    db.add(theme)
    db.flush()

    game_map = GameMap(
        name="Cumbernauld",
        description="Initial pilot map. This can be replaced by administrators.",
    )
    db.add(game_map)
    db.flush()

    locations = [
        ("Town Centre", 0.50, 0.45),
        ("The Link", 0.72, 0.62),
        ("Underpass", 0.30, 0.64),
        ("Library", 0.43, 0.28),
        ("Sports Centre", 0.78, 0.78),
    ]

    for name, x, y in locations:
        db.add(
            MapLocation(
                map_id=game_map.id,
                name=name,
                x=x,
                y=y,
            )
        )

    programme = Programme(
        name="Cumbernauld Youth Challenge",
        description="Six month digital youth work pilot.",
        start_date=date.today(),
        target_xp=1500000,
        active_theme_id=theme.id,
        active_map_id=game_map.id,
        active=True,
    )
    db.add(programme)
    db.flush()

    phases = [
        ("Art", "Creativity, design and community spaces.", "#9B51E0", "palette"),
        ("Civic Safety", "Recognising risk and keeping your squad safe.", "#F2994A", "shield"),
        ("Sport", "Sport, fitness and wellbeing.", "#2F80ED", "trophy"),
        ("Digital Bystander", "Online-to-offline safety and de-escalation.", "#00A6A6", "smartphone"),
    ]

    for index, (name, description, colour, icon) in enumerate(phases):
        db.add(
            Phase(
                programme_id=programme.id,
                name=name,
                description=description,
                colour=colour,
                icon=icon,
                sort_order=index,
            )
        )

    group = YouthGroup(
        programme_id=programme.id,
        name="Pilot Group",
    )
    db.add(group)
    db.flush()

    rules = [
        ("Attendance", "ATTENDANCE", 500, 500),
        ("Daily Behaviour", "BEHAVIOUR", 1000, 1000),
        ("Processing Chat", "PROCESSING_CHAT", 1200, 1200),
        ("Game Participation", "GAME_PARTICIPATION", 300, 300),
        ("Community Action", "COMMUNITY_ACTION", 5000, 5000),
    ]

    for name, code, individual, group_xp in rules:
        db.add(
            PointRule(
                programme_id=programme.id,
                name=name,
                code=code,
                individual_xp=individual,
                group_xp=group_xp,
            )
        )

    admin = User(
        username="admin",
        password_hash=hash_password("ChangeMe123!"),
        role="admin",
    )
    db.add(admin)

    staff = User(
        username="youthworker",
        password_hash=hash_password("ChangeMe123!"),
        role="youth_worker",
    )
    db.add(staff)

    player_user = User(
        username="player01",
        password_hash=hash_password("ChangeMe123!"),
        role="player",
    )
    db.add(player_user)
    db.flush()

    player = Player(
        user_id=player_user.id,
        group_id=group.id,
        gamertag="NightRider",
        avatar="avatar-1",
        programme_id=programme.id,
    )
    db.add(player)
    db.flush()

    skill = SkillTree(
        player_id=player.id,
        name="Personal Goal",
        description="Your current skill tree goal.",
    )
    db.add(skill)
    db.flush()

    milestones = [
        ("First Step", 15000, "£5 voucher"),
        ("Progress", 40000, "£10 voucher"),
        ("Mastery", 75000, "£20 voucher"),
    ]

    for name, xp, reward in milestones:
        db.add(
            SkillMilestone(
                skill_tree_id=skill.id,
                name=name,
                required_xp=xp,
                reward_description=reward,
            )
        )

    db.commit()

    print("")
    print("==========================================")
    print(" Digital Youth Platform")
    print(" Initial database created")
    print("==========================================")
    print("")
    print("Admin:")
    print("  username: admin")
    print("  password: ChangeMe123!")
    print("")
    print("Youth worker:")
    print("  username: youthworker")
    print("  password: ChangeMe123!")
    print("")
    print("Player:")
    print("  username: player01")
    print("  password: ChangeMe123!")
    print("")
    print("IMPORTANT: change these passwords.")
    print("")

else:
    print("Database already contains data. Nothing seeded.")

db.close()
