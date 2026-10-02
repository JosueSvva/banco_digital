from sqlalchemy import Column, Integer, String, Numeric, ForeignKey,LargeBinary
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key= True)
    nome = Column(String,nullable=False)
    email = Column(String, nullable=False, unique=True)
    cpf_criptografado = Column(LargeBinary, nullable=True)
    cpf_hash = Column(String, nullable=True, unique=True)
    senha_hash = Column(String, nullable=False)

