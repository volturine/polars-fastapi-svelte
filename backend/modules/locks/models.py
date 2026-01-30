from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Lock(Base):
    __tablename__ = 'locks'

    resource_id: Mapped[str] = mapped_column(String, primary_key=True)
    client_id: Mapped[str] = mapped_column(String, nullable=False)
    client_signature: Mapped[str] = mapped_column(String, nullable=False)
    lock_token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    acquired_at: Mapped[datetime] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    last_heartbeat: Mapped[datetime] = mapped_column(nullable=False)
