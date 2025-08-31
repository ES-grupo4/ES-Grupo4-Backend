from pydantic import BaseModel, ConfigDict


class AlunosRegistrados(BaseModel):
    total: int
    pos_graduacao: int
    em_graduacao: int
    ambos: int
    bolsistas: int


class PorTipoCliente(BaseModel):
    total: int
    externos: int
    professores: int
    tecnicos: int
    alunos: AlunosRegistrados


class RelatorioOut(BaseModel):
    nome_empresa: str
    faturamento_bruto_mensal: int

    clientes_registrados: PorTipoCliente

    funcionarios_ativos: int
    administradores_ativos: int
    desativados: int
    funcionarios_adicionados_mes: int
    # seria interessante um desativados no mês?

    compras_por_tipo: PorTipoCliente

    faturamento_por_tipo: PorTipoCliente

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "nome_empresa": "RU massa",
                "faturamento_bruto_mensal": 123495495,
                "clientes_registrados": {
                    "total": 100,
                    "externos": 1,
                    "professores": 10,
                    "tecnicos": 20,
                    "alunos": {
                        "total": 69,
                        "em_graduacao": 60,
                        "pos_graduacao": 7,
                        "ambos": 2,
                        "bolsistas": 30,
                    },
                },
                "funcionarios_ativos": 30,
                "administradores_ativos": 3,
                "desativados": 0,
                "funcionarios_adicionados_mes": 0,
                "compras_por_tipo": {
                    "total": 12000,
                    "externos": 10,
                    "professores": 150,
                    "tecnicos": 400,
                    "alunos": {
                        "total": 650,
                        "em_graduacao": 648,
                        "pos_graduacao": 1,
                        "ambos": 1,
                        "bolsistas": 400,
                    },
                },
            }
        },
    )
