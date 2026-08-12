from fastapi import APIRouter, HTTPException 
from schemas.request import RequestSchema
from schemas.response import ExtracaoSchema, FornecedorSchema, VeiculoSchema, ContratoSchema, ModalidadeSchema, RegraSchema, CondicaoRegraSchema 
from services.processador_pdf import extrair_texto_contrato
from services.extrator import extrair_dados_contrato, carregar_prompt

extraction_router = APIRouter(prefix="/extrair", tags=["Extração"])

@extraction_router.post("/")
async def extrair_texto(file_path: RequestSchema):
    """
    Rota padrão extração de textos e regras dos contratos de terceiros.
    """

    # Validar para ver se é realmente em formato PDF


    # Etapa 1: extrai o texto do contratp
    paginas_extraidas = extrair_texto_contrato(file_path.ds_caminho_arquivo)
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


"""
Ordem da rota:
1. Receber o caminho do arquivo (ou id do contrato)
2. Chamar a função extrair_dados_contrato 
3. receber o retorno de texto
4. Mandar ao gemini (arquivo com provável função de extração de regras)
5. pegar o retorno em json
6. retornar isso da api
7. verificação de erros


"""