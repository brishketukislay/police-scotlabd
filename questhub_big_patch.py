#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

def backup(p):
    b=p.with_suffix(p.suffix+'.questhub.bak')
    if not b.exists(): shutil.copy2(p,b)

def find(root,rel):
    p=root/rel
    if p.exists(): return p
    hits=[x for x in root.rglob(Path(rel).name) if x.as_posix().endswith(rel)]
    if len(hits)==1:return hits[0]
    raise FileNotFoundError(rel)

def rep(s,old,new,label):
    if old not in s: raise RuntimeError('Missing block: '+label)
    return s.replace(old,new,1)

def ins(s,marker,block,label):
    if marker not in s: raise RuntimeError('Missing marker: '+label)
    return s.replace(marker,block+'\n\n'+marker,1)

def patch_models(root):
    p=find(root,'app/db/models/core.py'); s=p.read_text()
    if 'class PlayerAttendanceToken' not in s:
        marker='# ============================================================================\n# ATTENDANCE\n# ============================================================================'
        block='''class PlayerAttendanceToken(Base):
    __tablename__ = "player_attendance_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    rotated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    player: Mapped["Player"] = relationship("Player", back_populates="attendance_token")
'''
        s=ins(s,marker,block,'attendance model')
        old="""    user: Mapped["User"] = relationship(
        "User",
        back_populates="player",
    )
"""
        new="""    user: Mapped["User"] = relationship(
        "User",
        back_populates="player",
    )

    attendance_token: Mapped[Optional["PlayerAttendanceToken"]] = relationship(
        "PlayerAttendanceToken",
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan",
    )
"""
        s=rep(s,old,new,'player relationship'); backup(p); p.write_text(s)
    p=find(root,'app/db/models/__init__.py'); s=p.read_text()
    if 'PlayerAttendanceToken' not in s:
        s=s.replace('    YouthGroup,\n)', '    YouthGroup,\n    PlayerAttendanceToken,\n)')
        s=s.replace('    "YouthGroup",\n','    "YouthGroup",\n    "PlayerAttendanceToken",\n')
        backup(p); p.write_text(s)

def patch_startup(root):
    p=find(root,'app/main.py'); s=p.read_text()
    if 'Base.metadata.create_all(bind=engine)' not in s:
        s=ins(s,'app = FastAPI(','Base.metadata.create_all(bind=engine)','FastAPI marker')
        backup(p); p.write_text(s)

def patch_reward_games(root):
    p=find(root,'app/routers/reward_games.py'); s=p.read_text(); backup(p)
    s=rep(s,'    Programme,\n    RewardGame,\n','    Programme,\n    YouthGroup,\n    RewardGame,\n','YouthGroup import')
    s=rep(s,'class GrantRewardGameRequest(BaseModel):\n    player_id: int\n','class GrantRewardGameRequest(BaseModel):\n    player_id: int | None = None\n    group_id: int | None = None\n','grant schema')
    s=rep(s,'def serialize_game(\n    game: RewardGame,\n    now: datetime | None = None,\n):','def serialize_game(\n    game: RewardGame,\n    now: datetime | None = None,\n    *,\n    include_prizes: bool = False,\n):','serializer')
    s=rep(s,'        "game_type": game.game_type.value,\n        "prize_values": game.prize_values,\n','        "game_type": game.game_type.value,\n        **({"prize_values": game.prize_values} if include_prizes else {}),\n','hide prizes')
    s=s.replace('**serialize_game(game, now),\n            "play_id": entitlement.id,','**serialize_game(game, now, include_prizes=False),\n            "play_id": entitlement.id,')
    marker='# ---------------------------------------------------------------------------\n# ADMIN\n# ---------------------------------------------------------------------------'
    start=s.index(marker)
    admin='''# ---------------------------------------------------------------------------
# ADMIN / STAFF REWARD GAMES
# ---------------------------------------------------------------------------

@router.get("/admin")
def admin_reward_games(user=Depends(require_roles("admin","youth_worker")), db:Session=Depends(get_db)):
    programme=db.query(Programme).filter(Programme.active.is_(True)).order_by(Programme.id.asc()).first()
    if not programme: return []
    games=db.query(RewardGame).filter(RewardGame.programme_id==programme.id).order_by(RewardGame.starts_at.desc(),RewardGame.id.desc()).all()
    out=[]
    for game in games:
        available=db.query(PlayerRewardGame).filter(PlayerRewardGame.game_id==game.id,PlayerRewardGame.status==RewardGamePlayStatus.AVAILABLE).count()
        played=db.query(PlayerRewardGame).filter(PlayerRewardGame.game_id==game.id,PlayerRewardGame.status==RewardGamePlayStatus.PLAYED).count()
        out.append({**serialize_game(game,include_prizes=True),"available_entitlements":available,"played_entitlements":played})
    return out

@router.get("/admin/targets")
def reward_game_targets(user=Depends(require_roles("admin","youth_worker")), db:Session=Depends(get_db)):
    programme=db.query(Programme).filter(Programme.active.is_(True)).order_by(Programme.id.asc()).first()
    if not programme: return {"players":[],"groups":[]}
    players=db.query(Player).filter(Player.programme_id==programme.id,Player.active.is_(True)).order_by(Player.gamertag.asc()).all()
    groups=db.query(YouthGroup).filter(YouthGroup.programme_id==programme.id,YouthGroup.active.is_(True)).order_by(YouthGroup.name.asc()).all()
    return {"players":[{"id":p.id,"gamertag":p.gamertag,"avatar":p.avatar,"group_id":p.group_id} for p in players],"groups":[{"id":g.id,"name":g.name} for g in groups]}

class RewardGameUpdateRequest(BaseModel):
    name: str | None = Field(default=None,min_length=2,max_length=200)
    description: str | None = Field(default=None,max_length=2000)
    prize_values: list[int] | None = Field(default=None,min_length=1,max_length=20)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    active: bool | None = None
    show_upcoming: bool | None = None

@router.post("/admin")
def create_reward_game(data:RewardGameCreateRequest,user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    if data.starts_at and data.ends_at and data.ends_at<=data.starts_at: raise HTTPException(status_code=400,detail="End time must be after start time.")
    programme=db.query(Programme).filter(Programme.active.is_(True)).order_by(Programme.id.asc()).first()
    if not programme: raise HTTPException(status_code=404,detail="No active programme configured.")
    values=validate_prizes(data.prize_values)
    game=RewardGame(programme_id=programme.id,name=data.name.strip(),description=data.description.strip() if data.description else None,game_type=data.game_type,prize_values=values,starts_at=normalise_datetime(data.starts_at),ends_at=normalise_datetime(data.ends_at),active=data.active,show_upcoming=data.show_upcoming,created_by_user_id=user.id)
    db.add(game); db.flush()
    from ..db.models import AuditLog
    db.add(AuditLog(user_id=user.id,action="reward_game.created",entity_type="reward_game",entity_id=game.id,details=f"type={game.game_type.value};name={game.name};prizes={values}"))
    db.commit(); return serialize_game(game,include_prizes=True)

@router.put("/admin/{game_id}")
def update_reward_game(game_id:int,data:RewardGameUpdateRequest,user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    game=db.get(RewardGame,game_id)
    if not game: raise HTTPException(status_code=404,detail="Reward game not found.")
    starts=normalise_datetime(data.starts_at) if data.starts_at is not None else game.starts_at
    ends=normalise_datetime(data.ends_at) if data.ends_at is not None else game.ends_at
    if starts and ends and ends<=starts: raise HTTPException(status_code=400,detail="End time must be after start time.")
    if data.name is not None: game.name=data.name.strip()
    if data.description is not None: game.description=data.description.strip() or None
    if data.prize_values is not None: game.prize_values=validate_prizes(data.prize_values)
    if data.starts_at is not None: game.starts_at=starts
    if data.ends_at is not None: game.ends_at=ends
    if data.active is not None: game.active=data.active
    if data.show_upcoming is not None: game.show_upcoming=data.show_upcoming
    from ..db.models import AuditLog
    db.add(AuditLog(user_id=user.id,action="reward_game.updated",entity_type="reward_game",entity_id=game.id,details=f"name={game.name};active={game.active};starts={game.starts_at};ends={game.ends_at}"))
    db.commit(); return serialize_game(game,include_prizes=True)

@router.post("/admin/{game_id}/grant")
def grant_reward_game(game_id:int,data:GrantRewardGameRequest,user=Depends(require_roles("admin","youth_worker")),db:Session=Depends(get_db)):
    if bool(data.player_id)==bool(data.group_id): raise HTTPException(status_code=400,detail="Provide exactly one of player_id or group_id.")
    game=db.get(RewardGame,game_id)
    if not game or not game.active: raise HTTPException(status_code=404,detail="Reward game not found or paused.")
    if data.player_id is not None:
        players=db.query(Player).filter(Player.id==data.player_id,Player.programme_id==game.programme_id,Player.active.is_(True)).all()
    else:
        group=db.query(YouthGroup).filter(YouthGroup.id==data.group_id,YouthGroup.programme_id==game.programme_id,YouthGroup.active.is_(True)).first()
        if not group: raise HTTPException(status_code=404,detail="Group not found.")
        players=db.query(Player).filter(Player.group_id==group.id,Player.programme_id==game.programme_id,Player.active.is_(True)).all()
    if not players: raise HTTPException(status_code=404,detail="No eligible active players found.")
    created=[]; skipped=0
    for player in players:
        existing=db.query(PlayerRewardGame).filter(PlayerRewardGame.game_id==game.id,PlayerRewardGame.player_id==player.id,PlayerRewardGame.status==RewardGamePlayStatus.AVAILABLE).first()
        if existing: skipped+=1; continue
        e=PlayerRewardGame(game_id=game.id,player_id=player.id,status=RewardGamePlayStatus.AVAILABLE,granted_by_user_id=user.id)
        db.add(e); db.flush(); created.append(e)
    from ..db.models import AuditLog
    target=f"player_id={data.player_id}" if data.player_id is not None else f"group_id={data.group_id}"
    db.add(AuditLog(user_id=user.id,action="reward_game.granted",entity_type="reward_game",entity_id=game.id,details=f"{target};created={len(created)};skipped={skipped}"))
    db.commit(); return {"success":True,"game_id":game.id,"assigned_count":len(created),"skipped_existing":skipped,"play_ids":[x.id for x in created]}
'''
    s=s[:start]+admin+'\n'; p.write_text(s)

def patch_admin(root):
    p=find(root,'app/routers/admin.py'); s=p.read_text(); backup(p)
    marker='# ============================================================\n# SIMPLE ADMIN DATA ENDPOINTS\n# ============================================================'
    if 'class AdminUserCreateRequest' not in s:
        block=r'''# ============================================================
# ACCOUNT MANAGEMENT
# ============================================================

class AdminUserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=10, max_length=200)
    role: str = Field(..., pattern=r"^(admin|youth_worker|player)$")
    display_name: str | None = Field(default=None, max_length=200)
    gamertag: str | None = Field(default=None, min_length=2, max_length=100)
    avatar: str = Field(default="avatar-01", max_length=100)
    group_id: int | None = None
    active: bool = True
    public_visible: bool = True

class AdminUserUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=100)
    password: str | None = Field(default=None, min_length=10, max_length=200)
    role: str | None = Field(default=None, pattern=r"^(admin|youth_worker|player)$")
    display_name: str | None = Field(default=None, max_length=200)
    active: bool | None = None
    suspended: bool | None = None
    public_visible: bool | None = None
    gamertag: str | None = Field(default=None, min_length=2, max_length=100)
    avatar: str | None = None
    group_id: int | None = None

def _user_payload(u,p=None):
    return {"id":u.id,"username":u.username,"role":u.role,"display_name":u.display_name,"active":u.active,"player":({"id":p.id,"gamertag":p.gamertag,"avatar":p.avatar,"active":p.active,"suspended":p.suspended,"public_visible":p.public_visible,"group_id":p.group_id,"programme_id":p.programme_id} if p else None)}

@router.get("/users")
def admin_users(user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    rows=db.query(User,Player).outerjoin(Player,Player.user_id==User.id).order_by(User.role,User.username).all()
    return [_user_payload(u,p) for u,p in rows]

@router.post("/users")
def admin_create_user(data:AdminUserCreateRequest,user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    username=data.username.strip()
    if db.query(User).filter(User.username==username).first(): raise HTTPException(status_code=409,detail="Username already exists.")
    programme=get_programme(db)
    if data.role=="player":
        if not data.gamertag: raise HTTPException(status_code=400,detail="Gamertag is required for a young person.")
        if db.query(Player).filter(Player.gamertag==data.gamertag.strip()).first(): raise HTTPException(status_code=409,detail="Gamertag already exists.")
        if data.group_id:
            group=db.query(YouthGroup).filter(YouthGroup.id==data.group_id,YouthGroup.programme_id==programme.id,YouthGroup.active.is_(True)).first()
            if not group: raise HTTPException(status_code=400,detail="Group not found or inactive.")
    u=User(username=username,password_hash=hash_password(data.password),role=data.role,display_name=data.display_name.strip() if data.display_name else None,active=data.active)
    db.add(u); db.flush(); p=None
    if data.role=="player":
        p=Player(user_id=u.id,programme_id=programme.id,group_id=data.group_id,gamertag=data.gamertag.strip(),avatar=data.avatar,active=data.active,public_visible=data.public_visible,suspended=False); db.add(p); db.flush()
    audit(db,user.id,"account.created",f"user_id={u.id};role={u.role}"); db.commit(); return _user_payload(u,p)

@router.put("/users/{user_id}")
def admin_update_user(user_id:int,data:AdminUserUpdateRequest,user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(status_code=404,detail="User not found.")
    if u.id==user.id and data.active is False: raise HTTPException(status_code=400,detail="You cannot deactivate your own account.")
    if u.id==user.id and data.role and data.role!="admin": raise HTTPException(status_code=400,detail="You cannot remove your own admin role.")
    if data.username is not None:
        name=data.username.strip()
        if db.query(User).filter(User.username==name,User.id!=u.id).first(): raise HTTPException(status_code=409,detail="Username already exists.")
        u.username=name
    if data.password: u.password_hash=hash_password(data.password)
    if data.display_name is not None: u.display_name=data.display_name.strip() or None
    if data.role is not None: u.role=data.role
    if data.active is not None: u.active=data.active
    p=db.query(Player).filter(Player.user_id==u.id).first()
    if u.role=="player" and p is None:
        programme=get_programme(db)
        if not data.gamertag: raise HTTPException(status_code=400,detail="Gamertag required for player.")
        p=Player(user_id=u.id,programme_id=programme.id,group_id=data.group_id,gamertag=data.gamertag.strip(),avatar=data.avatar or "avatar-01",active=u.active,public_visible=True,suspended=False); db.add(p)
    elif p is not None:
        if data.gamertag is not None:
            if db.query(Player).filter(Player.gamertag==data.gamertag.strip(),Player.id!=p.id).first(): raise HTTPException(status_code=409,detail="Gamertag already exists.")
            p.gamertag=data.gamertag.strip()
        if data.avatar is not None: p.avatar=data.avatar
        if data.group_id is not None: p.group_id=data.group_id
        if data.active is not None: p.active=data.active
        if data.suspended is not None: p.suspended=data.suspended
        if data.public_visible is not None: p.public_visible=data.public_visible
    audit(db,user.id,"account.updated",f"user_id={u.id};role={u.role};active={u.active}"); db.commit(); return _user_payload(u,p)

@router.post("/users/{user_id}/pause")
def admin_pause_user(user_id:int,user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(status_code=404,detail="User not found.")
    if u.id==user.id: raise HTTPException(status_code=400,detail="You cannot pause your own account.")
    u.active=False; p=db.query(Player).filter(Player.user_id==u.id).first()
    if p: p.active=False
    audit(db,user.id,"account.paused",f"user_id={u.id}"); db.commit(); return {"success":True,"user_id":u.id,"active":False}

@router.post("/users/{user_id}/reactivate")
def admin_reactivate_user(user_id:int,user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(status_code=404,detail="User not found.")
    u.active=True; p=db.query(Player).filter(Player.user_id==u.id).first()
    if p: p.active=True
    audit(db,user.id,"account.reactivated",f"user_id={u.id}"); db.commit(); return {"success":True,"user_id":u.id,"active":True}

@router.post("/players/{player_id}/suspend")
def admin_suspend_player(player_id:int,user=Depends(require_roles("admin","youth_worker")),db:Session=Depends(get_db)):
    p=db.get(Player,player_id)
    if not p: raise HTTPException(status_code=404,detail="Player not found.")
    p.suspended=True; audit(db,user.id,"player.suspended",f"player_id={p.id}"); db.commit(); return {"success":True,"player_id":p.id,"suspended":True}

@router.post("/players/{player_id}/unsuspend")
def admin_unsuspend_player(player_id:int,user=Depends(require_roles("admin","youth_worker")),db:Session=Depends(get_db)):
    p=db.get(Player,player_id)
    if not p: raise HTTPException(status_code=404,detail="Player not found.")
    p.suspended=False; audit(db,user.id,"player.unsuspended",f"player_id={p.id}"); db.commit(); return {"success":True,"player_id":p.id,"suspended":False}

class EconomySettingsRequest(BaseModel):
    jackpot_target_xp: int = Field(default=1500000, ge=1)
    max_group_penalty_percent: int = Field(default=10, ge=0, le=100)
    max_staff_multiplier: float = Field(default=1.3, ge=1, le=10)
    weekly_growth_cap_multiplier: float = Field(default=1.1, ge=1, le=10)
    group_penalties_enabled: bool = True
    multipliers_enabled: bool = True

@router.get("/economy")
def admin_economy(user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    from sqlalchemy import text
    programme=get_programme(db)
    db.execute(text("CREATE TABLE IF NOT EXISTS programme_economies (id INTEGER PRIMARY KEY, programme_id INTEGER NOT NULL UNIQUE, jackpot_target_xp INTEGER NOT NULL DEFAULT 1500000, max_group_penalty_percent INTEGER NOT NULL DEFAULT 10, max_staff_multiplier REAL NOT NULL DEFAULT 1.3, weekly_growth_cap_multiplier REAL NOT NULL DEFAULT 1.1, group_penalties_enabled BOOLEAN NOT NULL DEFAULT 1, multipliers_enabled BOOLEAN NOT NULL DEFAULT 1, updated_at DATETIME NOT NULL)"))
    row=db.execute(text("SELECT id,programme_id,jackpot_target_xp,max_group_penalty_percent,max_staff_multiplier,weekly_growth_cap_multiplier,group_penalties_enabled,multipliers_enabled FROM programme_economies WHERE programme_id=:pid"),{"pid":programme.id}).mappings().first()
    if not row:
        db.execute(text("INSERT INTO programme_economies (programme_id,updated_at) VALUES (:pid,CURRENT_TIMESTAMP)"),{"pid":programme.id}); db.commit()
        row=db.execute(text("SELECT id,programme_id,jackpot_target_xp,max_group_penalty_percent,max_staff_multiplier,weekly_growth_cap_multiplier,group_penalties_enabled,multipliers_enabled FROM programme_economies WHERE programme_id=:pid"),{"pid":programme.id}).mappings().first()
    return dict(row)

@router.put("/economy")
def update_admin_economy(data:EconomySettingsRequest,user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    from sqlalchemy import text
    programme=get_programme(db)
    db.execute(text("CREATE TABLE IF NOT EXISTS programme_economies (id INTEGER PRIMARY KEY, programme_id INTEGER NOT NULL UNIQUE, jackpot_target_xp INTEGER NOT NULL DEFAULT 1500000, max_group_penalty_percent INTEGER NOT NULL DEFAULT 10, max_staff_multiplier REAL NOT NULL DEFAULT 1.3, weekly_growth_cap_multiplier REAL NOT NULL DEFAULT 1.1, group_penalties_enabled BOOLEAN NOT NULL DEFAULT 1, multipliers_enabled BOOLEAN NOT NULL DEFAULT 1, updated_at DATETIME NOT NULL)"))
    db.execute(text("INSERT OR IGNORE INTO programme_economies (programme_id,updated_at) VALUES (:pid,CURRENT_TIMESTAMP)"),{"pid":programme.id})
    db.execute(text("UPDATE programme_economies SET jackpot_target_xp=:target,max_group_penalty_percent=:penalty,max_staff_multiplier=:mult,weekly_growth_cap_multiplier=:growth,group_penalties_enabled=:gp,multipliers_enabled=:mp,updated_at=CURRENT_TIMESTAMP WHERE programme_id=:pid"),{"pid":programme.id,"target":data.jackpot_target_xp,"penalty":data.max_group_penalty_percent,"mult":data.max_staff_multiplier,"growth":data.weekly_growth_cap_multiplier,"gp":data.group_penalties_enabled,"mp":data.multipliers_enabled})
    programme.target_xp=data.jackpot_target_xp; programme.max_group_penalty_percent=data.max_group_penalty_percent
    audit(db,user.id,"economy.updated",f"programme_id={programme.id};target={data.jackpot_target_xp}"); db.commit(); return {"success":True}
'''
        s=ins(s,marker,block,'admin marker')
    p.write_text(s)

def patch_attendance(root):
    p=find(root,'app/routers/attendance.py'); s=p.read_text(); backup(p)
    s=s.replace('from datetime import datetime, timedelta\nimport secrets\n','from datetime import datetime, timedelta\nimport hashlib\nimport secrets\n')
    s=s.replace('    Player,\n    Programme,\n','    Player,\n    PlayerAttendanceToken,\n    Programme,\n')
    marker='# ============================================================\n# STAFF ATTENDANCE SESSION\n# ============================================================'
    if '@router.post("/scan-player-qr")' not in s:
        block=r'''# ============================================================
# PERSONAL PLAYER QR
# ============================================================

def _qr_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

@router.post("/player-qr/rotate")
def rotate_player_qr(user=Depends(require_roles("player")), db:Session=Depends(get_db)):
    player=db.query(Player).filter(Player.user_id==user.id,Player.active.is_(True)).first()
    if not player: raise HTTPException(status_code=404,detail="Player profile not found.")
    raw=secrets.token_urlsafe(32)
    token=db.query(PlayerAttendanceToken).filter(PlayerAttendanceToken.player_id==player.id).first()
    if not token:
        token=PlayerAttendanceToken(player_id=player.id,token_hash=_qr_hash(raw),active=True); db.add(token)
    else:
        token.token_hash=_qr_hash(raw); token.active=True; token.rotated_at=datetime.utcnow()
    db.commit(); return {"success":True,"token":raw,"format":"questhub-attendance-v1"}

@router.get("/player-qr")
def player_qr(user=Depends(require_roles("player")), db:Session=Depends(get_db)):
    player=db.query(Player).filter(Player.user_id==user.id,Player.active.is_(True)).first()
    if not player: raise HTTPException(status_code=404,detail="Player profile not found.")
    raw=secrets.token_urlsafe(32)
    token=db.query(PlayerAttendanceToken).filter(PlayerAttendanceToken.player_id==player.id).first()
    if not token:
        token=PlayerAttendanceToken(player_id=player.id,token_hash=_qr_hash(raw),active=True); db.add(token)
    else:
        token.token_hash=_qr_hash(raw); token.active=True; token.rotated_at=datetime.utcnow()
    db.commit()
    return {"success":True,"token":raw,"format":"questhub-attendance-v1"}

class StaffScanQRRequest(BaseModel):
    token: str = Field(...,min_length=10,max_length=200)
    session_id: int | None = None

@router.post("/scan-player-qr")
def scan_player_qr(payload:StaffScanQRRequest,user=Depends(require_roles("admin","youth_worker")),db:Session=Depends(get_db)):
    token=db.query(PlayerAttendanceToken).filter(PlayerAttendanceToken.token_hash==_qr_hash(payload.token.strip()),PlayerAttendanceToken.active.is_(True)).first()
    if not token: raise HTTPException(status_code=404,detail="Attendance QR is invalid or rotated.")
    player=db.query(Player).filter(Player.id==token.player_id,Player.active.is_(True)).first()
    if not player or player.suspended: raise HTTPException(status_code=400,detail="Player is not eligible for attendance.")
    session=db.get(AttendanceSession,payload.session_id) if payload.session_id else None
    if session is None:
        session=db.query(AttendanceSession).filter(AttendanceSession.programme_id==player.programme_id,AttendanceSession.active.is_(True)).order_by(AttendanceSession.id.desc()).first()
    if not session: raise HTTPException(status_code=404,detail="No active attendance session.")
    if session.programme_id!=player.programme_id: raise HTTPException(status_code=400,detail="Player and session are in different programmes.")
    if session.group_id is not None and session.group_id!=player.group_id: raise HTTPException(status_code=400,detail="Player is not eligible for this group session.")
    try:
        attendance=check_in(db,player=player,attendance_session=session,created_by=user.id); db.commit(); db.refresh(attendance)
        return {"success":True,"attendance_id":attendance.id,"player":{"id":player.id,"gamertag":player.gamertag,"avatar":player.avatar},"session_id":session.id,"xp_awarded":attendance.xp_awarded,"checked_in_at":attendance.checked_in_at}
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400,detail=str(exc)) from exc
'''
        s=ins(s,marker,block,'attendance marker')
    p.write_text(s)

def patch_gamification(root):
    p=find(root,'app/services/gamification.py'); s=p.read_text()
    if 'from sqlalchemy import and_, or_, func' not in s:
        s=s.replace('from sqlalchemy import and_, or_\n','from sqlalchemy import and_, or_, func\n'); backup(p); p.write_text(s)

def patch_frontend(root):
    src=next((x for x in [root/'frontend'/'src',root/'src'] if (x/'api.ts').exists()),None)
    if not src:return
    p=src/'api.ts'; s=p.read_text()
    if 'adminUsers:' not in s:
        add='''
  adminUsers: () => request<any[]>("/api/admin/users"),
  createAdminUser: (payload:any) => request<any>("/api/admin/users", {method:"POST",body:JSON.stringify(payload)}),
  updateAdminUser: (id:number,payload:any) => request<any>(`/api/admin/users/${id}`, {method:"PUT",body:JSON.stringify(payload)}),
  pauseAdminUser: (id:number) => request<any>(`/api/admin/users/${id}/pause`, {method:"POST"}),
  reactivateAdminUser: (id:number) => request<any>(`/api/admin/users/${id}/reactivate`, {method:"POST"}),
  suspendPlayer: (id:number) => request<any>(`/api/admin/players/${id}/suspend`, {method:"POST"}),
  unsuspendPlayer: (id:number) => request<any>(`/api/admin/players/${id}/unsuspend`, {method:"POST"}),
  economy: () => request<any>("/api/admin/economy"),
  updateEconomy: (payload:any) => request<any>("/api/admin/economy", {method:"PUT",body:JSON.stringify(payload)}),
  rewardGameTargets: () => request<any>("/api/reward-games/admin/targets"),
  updateRewardGame: (id:number,payload:any) => request<any>(`/api/reward-games/admin/${id}`, {method:"PUT",body:JSON.stringify(payload)}),
  playerAttendanceQR: () => request<any>("/api/attendance/player-qr"),
  rotateAttendanceQR: () => request<any>("/api/attendance/player-qr/rotate",{method:"POST"}),
  scanPlayerQR: (token:string,session_id?:number) => request<any>("/api/attendance/scan-player-qr",{method:"POST",body:JSON.stringify({token,session_id})}),
'''
        s=s.replace('  jackpot: () => request<any>("/api/admin/jackpot"),','  jackpot: () => request<any>("/api/admin/jackpot"),\n'+add); backup(p); p.write_text(s)

def main():
    cwd=Path.cwd(); root=next((b for b in [cwd,cwd/'backend'] if (b/'app/routers/admin.py').exists()),None)
    if root is None:
        hits=list(cwd.rglob('app/routers/admin.py'))
        root=hits[0].parents[2] if hits else None
    if root is None: raise FileNotFoundError('QuestHub backend root not found.')
    print('QuestHub root:',root)
    patch_models(root); patch_startup(root); patch_reward_games(root); patch_admin(root); patch_attendance(root); patch_gamification(root); patch_frontend(root)
    print('BIG PATCH COMPLETE. Restart FastAPI. No DB deletion required.')

if __name__=='__main__':
    try: main()
    except Exception as e: print('PATCH FAILED:',e,file=sys.stderr); sys.exit(1)
