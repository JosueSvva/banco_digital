from pydantic import BaseModel


class UsuarioCadastro(BaseModel):
    nome : str
    cpf : str
    email : str
    senha : str

class UsuarioLogin(BaseModel):
    email : str
    senha : str