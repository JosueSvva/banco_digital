from sqlalchemy import create_engine # essa conexao configura a conexao do banco
from sqlalchemy.orm import DeclarativeBase, sessionmaker # cria sessoes para consultar e alterar dados, serve para base para nossas classes de modelo

DATABASE_URL = "sqlite:///./banco.db" # aqui eu criei a URL e defini o banco que vou usar que e banco.db

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    
)

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)