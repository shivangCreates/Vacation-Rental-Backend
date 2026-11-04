
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey,
)
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class PropertyDocument(Base):
    __tablename__ = "property_documents"

    id = Column(Integer, primary_key=True, index=True)

    property_id = Column(
        Integer,
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content = Column(Text, nullable=False)

    embedding = Column(Vector(768), nullable=False)

    chunk_index = Column(Integer, nullable=False, default=0)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
