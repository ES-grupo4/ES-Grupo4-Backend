from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt # type: ignore
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from ..models.models import Funcionario
from ..models.db_setup import conexao_bd
from ..schemas.auth import LoginDTO

auth_router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"],
)
router = auth_router

security = HTTPBearer()


# era pra isso ir pra um .env, perguntar pra Leo dps como a gente faz e ele cria uma chave melhor tb
CHAVE_SECRETA = "CHAVE_MUITO_DOIDA_XD"
ALGORITMO = "HS256"
TOKEN_EXPIRA_EM_MINUTOS = 30


def cria_token_de_acesso(funcionarioData: dict, expira_tempo: timedelta):
    to_encode = funcionarioData.copy()
    expira_em = datetime.now(timezone.utc) + expira_tempo
    to_encode.update({"exp": expira_em})
    encoded_jwt = jwt.encode(to_encode, CHAVE_SECRETA, ALGORITMO)
    return encoded_jwt


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


def get_usuario_por_cpf(db: conexao_bd, cpf: str):
    cpf = cpf.replace(".", "").replace("-", "")
    usuario = db.scalar(select(Funcionario).where(Funcionario.cpf == cpf))
    return usuario


@router.post(
    "/login",
    summary="Realiza autenticação do usuário no sistema",
    tags=["Autenticação"],
)
async def login(login_data: LoginDTO, db: conexao_bd):
    usuario = get_usuario_por_cpf(db, login_data.cpf)
    if usuario and login_data.senha == usuario.senha:
        token = cria_token_de_acesso(
            {"sub": usuario.cpf, "tipo": usuario.tipo},
            timedelta(minutes=TOKEN_EXPIRA_EM_MINUTOS),
        )
        return {"token": token}
    else:
        raise HTTPException(status_code=400, detail="Usuário ou senha incorretos")
