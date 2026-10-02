from fastapi import FastAPI, HTTPException,status
from app.schemas.usuario import UsuarioCadastro,UsuarioLogin
from app.database import SessionLocal
from app.models.usuario import Usuario
from app.models.conta import Conta
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from decimal import Decimal


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
     sessao.flush()
     conta_usuario = Conta(usuario_id = usuario1.id, saldo = Decimal("0.00"), numero_conta = 1000 + usuario1.id)
     sessao.add(conta_usuario)
     sessao.commit()
     return{"Mensagem":"Cadastro Realizado com Sucesso"}
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


@app.post("/Login")
def login (dados:UsuarioLogin):
    try:
        sessao = SessionLocal()
        login1 =sessao.query(Usuario).filter(Usuario.email == dados.email).first()
        if login1 == None:
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Email ou senha invalido.",
            )
        password_login = PasswordHash.recommended()
        senha_valida = password_login.verify(dados.senha, login1.senha_hash)
        if senha_valida == True:
                return "Login Realizado Com Sucesso."
        else:
                raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Email ou senha invalido."
            )
    finally:
        sessao.close()  
        print("Fechando sessao" )


@app.get("/saldo/{numero_conta}")
def saldo(numero_conta: int):
    try:
        sessao = SessionLocal()
        saldo1 = sessao.query(Conta).filter(Conta.numero_conta == numero_conta).first()
        if saldo1 == None:
            raise HTTPException(
                            status_code= status.HTTP_404_NOT_FOUND,
                            detail= "Conta Nao Encontrada.",
                        )
        return {
                "numero_conta" : saldo1.numero_conta,
                "Saldo" : saldo1.saldo
                }
    finally:
        sessao.close()
        print("Fechando sessao" )

@app.post("/deposito/{numero_conta}")
def deposito(numero_conta: int, valor: Decimal):
    try:
        sessao = SessionLocal()

        
        if valor <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O valor do deposito deve ser maior que zero."
            )


        conta = (
            sessao.query(Conta)
            .filter(Conta.numero_conta == numero_conta)
            .first()
        )
        if conta is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta nao encontrada."
            )
        conta.saldo += valor

        sessao.commit()

        sessao.refresh(conta)

        return {
        "numero_conta": conta.numero_conta,
        "valor_depositado": valor,
        "novo_saldo": conta.saldo
            }

    finally:
        sessao.close()
        print("Fechando sessao")

@app.post("/saque/{numero_conta}")
def saque(numero_conta: int, valor: Decimal):
    try:
        sessao = SessionLocal()

    
        if valor <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O valor do saque deve ser maior que zero."
            )

    
        conta = (
            sessao.query(Conta)
            .filter(Conta.numero_conta == numero_conta)
            .first()
        )

        
        if conta is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta nao encontrada."
            )

        
        if valor > conta.saldo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Saldo insuficiente."
            )

        
        conta.saldo -= valor

        
        sessao.commit()

        
        sessao.refresh(conta)

        return {
            "numero_conta": conta.numero_conta,
            "valor_sacado": valor,
            "novo_saldo": conta.saldo
        }

    finally:
        sessao.close()
        print("Fechando sessao")

@app.post("/transferencia")
def transferencia(
    conta_origem: int,
    conta_destino: int,
    valor: Decimal
):
    try:
        sessao = SessionLocal()

        if valor <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O valor da transferencia deve ser maior que zero."
            )

        if conta_origem == conta_destino:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A conta de origem e destino devem ser diferentes."
            )

        origem = (
            sessao.query(Conta)
            .filter(Conta.numero_conta == conta_origem)
            .first()
        )

        if origem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta de origem nao encontrada."
            )

        destino = (
            sessao.query(Conta)
            .filter(Conta.numero_conta == conta_destino)
            .first()
        )

        if destino is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conta de destino nao encontrada."
            )

        if valor > origem.saldo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Saldo insuficiente."
            )

        origem.saldo -= valor
        destino.saldo += valor

        sessao.commit()

        sessao.refresh(origem)
        sessao.refresh(destino)

        return {
            "mensagem": "Transferencia realizada com sucesso.",
            "conta_origem": origem.numero_conta,
            "conta_destino": destino.numero_conta,
            "valor_transferido": valor,
            "saldo_origem": origem.saldo,
            "saldo_destino": destino.saldo
        }

    finally:
        sessao.close()
        print("Fechando sessao")