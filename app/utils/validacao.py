from fastapi import HTTPException
from validate_docbr import CPF  # type: ignore

cpf = CPF()

def valida_e_retorna_cpf(usuario_cpf: str):
    usuario_cpf = usuario_cpf.replace(".", "").replace("-", "")

    if not cpf.validate(usuario_cpf):
        raise HTTPException(status_code=400, detail="CPF inválido")

    return usuario_cpf