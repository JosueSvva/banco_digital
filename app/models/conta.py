from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from app.database import Base


class Conta(Base):
    __tablename__ = "conta"
    id = Column(Integer,primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    saldo = Column(Numeric,nullable=False, default= 0.00)
    numero_conta = Column(Integer,nullable=False,unique=True)