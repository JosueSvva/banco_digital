from fastapi import FastAPI, HTTPException,status, Depends
from app.schemas.usuario import UsuarioCadastro,UsuarioLogin
from app.database import SessionLocal
from app.models.usuario import Usuario
from app.models.conta import Conta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from app.models.transasao import Transacao
from sqlalchemy import text
import os
import jwt
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
security = HTTPBearer()
def verificar_token(
    credenciais: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        token = credenciais.credentials

        dados = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        usuario_id = dados.get("sub")

        if usuario_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido."
            )

        return int(usuario_id)

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido."
        )

app = FastAPI()
def mascarar_cpf(cpf):
    return f"***.***.***-{cpf[-2:]}"
@app.get("/usuario/{usuario_id}")
def consultar_usuario(usuario_id: int):
    sessao = SessionLocal()

    try:
        chave = os.getenv("CPF_ENCRYPTION_KEY")

        usuario = sessao.query(Usuario).filter(
            Usuario.id == usuario_id
        ).first()

        if not usuario:
            raise HTTPException(
                status_code=404,
                detail="Usuario nao encontrado."
            )

        resultado = sessao.execute(
            text("""
                SELECT pgp_sym_decrypt(
                    :cpf_criptografado,
                    :chave
                )
            """),
            {
                "cpf_criptografado": usuario.cpf_criptografado,
                "chave": chave
            }
        ).fetchone()

        cpf = resultado[0]

        return {
            "nome": usuario.nome,
            "cpf": mascarar_cpf(cpf)
        }

    finally:
        sessao.close()

@app.get("/")
def inicio():
    return {"mensagem": "Banco Digital API"}



@app.post("/cadastro")
def cadastro (dados:UsuarioCadastro):
    try:
     sessao = SessionLocal()
     password_hash = PasswordHash.recommended()
     senha_hash = password_hash.hash(dados.senha)
     chave = os.getenv("CPF_ENCRYPTION_KEY")
     if not chave:
        raise RuntimeError("CPF_ENCRYPTION_KEY não configurada.")
     resultado = sessao.execute(
    text("""
        SELECT
            pgp_sym_encrypt(:cpf, :chave),
            encode(digest(:cpf, 'sha256'), 'hex')
    """),
    {
        "cpf": dados.cpf,
        "chave": chave
    }
).fetchone()
     cpf_criptografado, cpf_hash = resultado
     usuario1 = Usuario(
    nome=dados.nome,
    email=dados.email,
    cpf_criptografado=cpf_criptografado,
    cpf_hash=cpf_hash,
    senha_hash=senha_hash
    )
     sessao.add(usuario1)
     sessao.flush()
     conta_usuario = Conta(usuario_id = usuario1.id, saldo = Decimal("0.00"), numero_conta = 1000 + usuario1.id)
     sessao.add(conta_usuario)
     sessao.commit()
     return{"Mensagem":"Cadastro Realizado com Sucesso"}
    except IntegrityError as erro:
        print(erro)
        sessao.rollback()
        if "usuario_cpf_hash_key" in str(erro):
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
                agora = datetime.now(timezone.utc)
                expiracao = agora + timedelta(minutes=30)
                token = jwt.encode(
                    {
                    "sub": str(login1.id),
                     "email": login1.email,
                      "iat": agora,
                     "exp": expiracao
                    },
                SECRET_KEY,
                algorithm=ALGORITHM
             )

                return {
                "mensagem": "Login realizado com sucesso",
                "access_token": token,
                "token_type": "bearer"
                }
        else:
                raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Email ou senha invalido."
            )
    finally:
        sessao.close()  
        print("Fechando sessao" )


@app.get("/saldo/{numero_conta}")
def saldo(numero_conta: int,
          usuario_id: int = Depends(verificar_token)
          ):
    try:
        sessao = SessionLocal()
        saldo1 = sessao.query(Conta).filter(Conta.numero_conta == numero_conta).first()
        if saldo1 == None:
            raise HTTPException(
                            status_code= status.HTTP_404_NOT_FOUND,
                            detail= "Conta Nao Encontrada.",
                        )
        if saldo1.usuario_id != usuario_id:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail= "Voce nao tem permissao para acessar esta conta."
        )
        return {
                "numero_conta" : saldo1.numero_conta,
                "Saldo" : saldo1.saldo
                 }
    
    finally:
        sessao.close()
        print("Fechando sessao" )

@app.post("/deposito/{numero_conta}")
def deposito(numero_conta: int, valor: Decimal,
             usuario_id: int = Depends(verificar_token)
            ):
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
        if conta.usuario_id != usuario_id:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem permissao para acessar esta conta."
             )
        conta.saldo += valor
        transacao = Transacao(
        tipo_transacao="DEPOSITO",
        valor=valor,
        conta_destino_id=conta.id
            )

        sessao.add(transacao)

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
def saque(numero_conta: int, valor: Decimal,
          usuario_id: int = Depends(verificar_token)
          ):
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
        if conta.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voce nao tem permissao para acessar esta conta."
            )
        if valor > conta.saldo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Saldo insuficiente."
            )

        
        conta.saldo -= valor
        transacao = Transacao(
        tipo_transacao="SAQUE",
        valor=valor,
        conta_origem_id=conta.id
            )

        sessao.add(transacao)

        
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
    valor: Decimal,
    usuario_id: int = Depends(verificar_token)
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
        if origem.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voce nao tem permissao para movimentar esta conta."
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
        transacao = Transacao(
        tipo_transacao="TRANSFERENCIA",
        valor=valor,
        conta_origem_id=origem.id,
        conta_destino_id=destino.id
            )

        sessao.add(transacao)

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


@app.get("/extrato/{numero_conta}")
def extrato(numero_conta: int,
            usuario_id: int = Depends(verificar_token)
            ):
    try:
        sessao = SessionLocal()

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
        if conta.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voce nao tem permissao para acessar esta conta."
                )
        transacoes = (
            sessao.query(Transacao)
            .filter(
                (Transacao.conta_origem_id == conta.id) |
                (Transacao.conta_destino_id == conta.id)
            )
            .order_by(Transacao.data.desc())
            .all()
        )

        return [
            {
                "tipo": transacao.tipo_transacao,
                "valor": transacao.valor,
                "data": transacao.data
            }
            for transacao in transacoes
        ]

    finally:
        sessao.close()
        print("Fechando sessao")