from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

# Campos do retorno do json
class ExtracaoSchema(BaseModel):
    status: str = Field(description="'sucesso' ou 'falha'")
    confianca_geral: float = Field(ge=0, le=1, description="0 a 1")
    observacoes: list[str] = Field(default_factory=list)

    class Config():
        from_attributes = True

class FornecedorSchema(BaseModel):
    nm_fornecedor: str
    ds_cnpj_cpf: str

    class Config():
        from_attributes = True

class VeiculoSchema(BaseModel):
    nm_tipo_veiculo: Optional[str]

    class Config():
        from_attributes = True

class ContratoSchema(BaseModel):
    dt_vigencia_inicio: date
    dt_vigencia_fim: date

    class Config():
        from_attributes = True

class ModalidadeSchema(BaseModel):
    nm_tipo_corrida: Optional[str]

    class Config():
        from_attributes = True

class RegraSchema(BaseModel):
    nr_prioridade: int
    nm_regra: str
    nr_valor_km: Optional[float]
    nr_valor_fixo: Optional[float]
    nr_percentual: Optional[float]

    class Config():
        from_attributes = True

class CondicaoRegraSchema(BaseModel):
    ds_tipo_condicao: str = Field(description="Ex.: HORARIO, DIA_SEMANA, DISTANCIA_MINIMA")
    ds_valor: dict = Field(description="Objeto com os valores da condição")

    class Config():
        from_attributes = True

