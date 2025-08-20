from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt  # type: ignore
from datetime import datetime, timezone, timedelta
import hashlib
from cryptography.fernet import Fernet

security = HTTPBearer()
fernet = Fernet("7kT3Kk1-CFNKWgW6tp22bxlSo0qGwc8ZRjWiOUPR2JU=")

# Sessão de gerar hash de senhas - Início


def gerar_hash(str_decodificada: str):
    return hashlib.sha256(str_decodificada.encode("utf-8")).hexdigest()


def verificar_hash(senha_str: str, hash_str: str):
    return hashlib.sha256(senha_str.encode()).hexdigest() == hash_str


# Sessão de gerar hash de senhas - Fim

# Sessão de geração e confirmação de token - Início

# CONFIG
CHAVE_SECRETA = "CHAVE_MUITO_DOIDA_XD"
ALGORITMO = "HS256"
TOKEN_EXPIRA_EM_MINUTOS = 30


def cria_token_de_acesso(funcionarioData: dict):
    to_encode = funcionarioData.copy()
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRA_EM_MINUTOS)

    to_encode.update({"exp": expira_em})

    encoded_jwt = jwt.encode(to_encode, CHAVE_SECRETA, ALGORITMO)
    return encoded_jwt


def verifica_token_de_acesso(token: str):
    carga = jwt.decode(token, CHAVE_SECRETA, ALGORITMO)
    return carga.get("sub")


async def get_usuario_atual(
    credenciais: HTTPAuthorizationCredentials = Depends(security),
):
    credenciais_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
    )

    try:
        token = credenciais.credentials
        payload = jwt.decode(token, CHAVE_SECRETA, ALGORITMO)
        cpf: str | None = payload.get("sub")
        tipo: str | None = payload.get("tipo")
        if cpf is None or tipo is None:
            raise credenciais_exception

    except JWTError:
        raise credenciais_exception

    return {"cpf": cpf, "tipo": tipo}


# Sessão de geração e confirmação de token - Fim

# Sessão de criptografia de CPF - Início


def criptografa_cpf(cpf: str):
    return fernet.encrypt(cpf.encode())


def descriptografa_cpf(cpf_criptografado: bytes):
    return fernet.decrypt(cpf_criptografado).decode()


# Sessão de criptografia de CPF - Fim
