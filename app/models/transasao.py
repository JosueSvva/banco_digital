from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, DateTime
from datetime import datetime

from app.database import Base


class Transacao(Base):
    __tablename__ = "transacao"

    id = Column(Integer, primary_key=True)

    tipo_transacao = Column(String, nullable=False)

    valor = Column(Numeric(10, 2), nullable=False)

    conta_origem_id = Column(
        Integer,
        ForeignKey("conta.id"),
        nullable=True
    )

    conta_destino_id = Column(
        Integer,
        ForeignKey("conta.id"),
        nullable=True
    )

    data = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )