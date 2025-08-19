from fastapi import HTTPException, status
from validate_docbr import CPF  # type: ignore

cpf = CPF()

def valida_e_retorna_cpf(usuario_cpf: str):
    usuario_cpf = usuario_cpf.replace(".", "").replace("-", "")

    if not cpf.validate(usuario_cpf):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF inválido")

    return usuario_cpf