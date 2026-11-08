from app.database import Base

from sqlalchemy import String, LargeBinary, ForeignKey, Index
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)


class TreeBody(Base):
    __tablename__ = "tree_body"

    id: Mapped[int] = mapped_column(primary_key=True)

    tree_id: Mapped[int] = mapped_column(
        ForeignKey("tree_hdr.id"),
        nullable=False
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("tree_body.id"),
        nullable=True
    )

    ai_provider: Mapped[str | None] = mapped_column(String(30), nullable=True)

    ai_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    command: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    generation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed", server_default="completed")

    generation_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    image: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True
    )


# Only one root image per tree
Index(
    "uq_tree_body_one_root",
    TreeBody.tree_id,
    unique=True,
    postgresql_where=TreeBody.parent_id.is_(None)
)