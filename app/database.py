from sqlalchemy import create_engine # essa conexao configura a conexao do banco
from sqlalchemy.orm import DeclarativeBase, sessionmaker # cria sessoes para consultar e alterar dados, serve para base para nossas classes de modelo
from dotenv import load_dotenv
import os
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    
)

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)