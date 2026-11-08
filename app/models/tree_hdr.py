from app.database import Base

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)


class TreeHdr(Base):
    __tablename__ = "tree_hdr"

    id: Mapped[int] = mapped_column(primary_key=True)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

