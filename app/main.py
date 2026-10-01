from fastapi import FastAPI, HTTPException,status
from app.schemas.usuario import UsuarioCadastro
from app.database import SessionLocal
from app.models.usuario import Usuario
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError


app = FastAPI()

@app.get("/")
def inicio():
    return {"mensagem": "Banco Digital API"}



@app.post("/cadastro")
def cadastro (dados:UsuarioCadastro):
    try:
     sessao = SessionLocal()
     password_hash = PasswordHash.recommended()
     senha_hash = password_hash.hash(dados.senha)
     usuario1 = Usuario(nome = dados.nome,email = dados.email,cpf = dados.cpf,senha_hash = senha_hash)
     sessao.add(usuario1)
     sessao.commit()
     return{"mengsaem":usuario1}
    except IntegrityError as erro:
        print(erro)
        sessao.rollback()
        if "usuario.cpf" in str(erro):
         raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "Cpf Ja Cadastrado.",
          )
        else:
           if "usuario.email" in str (erro):
              raise HTTPException(
                          status_code = status.HTTP_409_CONFLICT,
                          detail = "email Ja Cadastrado.",
                        )
    finally: 
        sessao.close()  
        print("Fechando sessao" )

