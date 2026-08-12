from fastapi import APIRouter, HTTPException 
from schemas.request import RequestSchema
from services.processador_pdf import extrair_texto_pdf
from services.extrator import extrair_dados_contrato, carregar_prompt
from services.validador import validar_extracao

extraction_router = APIRouter(prefix="/extrair", tags=["Extração"])

@extraction_router.post("/")
async def extrair_texto(file_path: RequestSchema):
    """
    Rota padrão de extração de textos e regras dos contratos de terceiros.
    """

    # Validar para ver se é realmente em formato PDF


    # Etapa 1: extrai o texto do contrato
    paginas_extraidas = extrair_texto_pdf(file_path.caminho)

    print(paginas_extraidas)
    if not paginas_extraidas:
        raise HTTPException(status_code=400, detail="Falha na extração do texto do contrato.")

    # Etapa 2: limpar texto


    try:
        # Etapa 3: extrai dados
        dados_extraidos = extrair_dados_contrato(paginas_extraidas)

        # Etapa 4: valida os dados extraídos
        dados_validados = validar_extracao(dados_extraidos, paginas_extraidas)

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return dados_validados
        
