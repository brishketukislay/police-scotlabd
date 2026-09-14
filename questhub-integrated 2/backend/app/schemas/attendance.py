from datetime import datetime

from pydantic import BaseModel


class AttendanceCheckInRequest(BaseModel):
    session_id: int


class AttendanceResponse(BaseModel):
    id: int
    player_id: int
    session_id: int
    checked_in_at: datetime
    xp_awarded: int

    class Config:
        from_attributes = True
