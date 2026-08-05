from fastapi import APIRouter, HTTPException 
from schemas.request import RequestSchema
from schemas.response import ExtracaoSchema, FornecedorSchema, VeiculoSchema, ContratoSchema, ModalidadeSchema, RegraSchema, CondicaoRegraSchema 
from services.processador_pdf import extrair_texto_pdf
from services.extrator import extrair_dados_contrato, carregar_prompt

extraction_router = APIRouter(prefix="/extrair", tags=["Extração"])

@extraction_router.post("/")
async def extrair_texto(file_path: RequestSchema):
    """
    Rota padrão extração de textos e regras dos contratos de terceiros.
    """

    # Validar para ver se é realmente em formato PDF


    # Etapa 1: extrai o texto do contratp
    paginas_extraidas = extrair_texto_pdf(file_path.ds_caminho_arquivo)

    print(paginas_extraidas)
    if not paginas_extraidas:
        raise HTTPException(status_code=400, detail="Falha na extração do texto do contrato.")

    # Etapa 2: limpar texto

    # Etapa 3: enviar ao gemini
    try:
        dados_extraidos = extrair_dados_contrato(paginas_extraidas)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


    return {
        "Dados": dados_extraidos
        }
