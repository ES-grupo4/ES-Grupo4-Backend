from passlib.context import CryptContext  # type: ignore

pwd_context = CryptContext(schemes=["bcrypt"])


def gerar_hash(senha_str: str):
    return pwd_context.hash(senha_str)


def verificar_hash(senha_str: str, hash: str):
    return pwd_context.verify(senha_str, hash)
