from pydantic import BaseModel
from typing import Optional

# campo de entrada (verificar com karina como vai ser)
class RequestSchema(BaseModel):
    caminho: str # caminho do arquivo PDF
    # id_contrato: int # caso seja pelo id do contrato

    class Config():
        from_attributes = True
