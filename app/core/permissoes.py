from fastapi import Depends, HTTPException, status
from ..core.seguranca import get_usuario_atual


def requer_permissao(*tipo_permitidos: str):
    def dependency(usuario_atual: dict = Depends(get_usuario_atual)):
        if usuario_atual["tipo"] not in tipo_permitidos:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return usuario_atual

    return Depends(dependency)
