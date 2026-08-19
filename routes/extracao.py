from fastapi import APIRouter, File, HTTPException, UploadFile
from services.processador_pdf import extrair_texto_pdf
from services.extrator import extrair_dados_contrato
from services.validador import validar_extracao

extraction_router = APIRouter(prefix="/extrair", tags=["Extração"])

@extraction_router.post("/")
async def extrair_texto(file: UploadFile = File(..., description="Arquivo PDF do contrato em buffer")):
    """
    Rota padrão de extração de textos e regras dos contratos de terceiros a partir do buffer enviado.
    """
    # Validação do formato do arquivo
    nome_arquivo = file.filename or ""
    if not nome_arquivo.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="O arquivo enviado deve ser no formato PDF.")

    try:
        conteudo_buffer = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler o arquivo enviado: {str(e)}")

    if not conteudo_buffer:
        raise HTTPException(status_code=400, detail="O arquivo enviado está vazio.")

    # Etapa 1: extrai o texto do contrato a partir do buffer
    try:
        paginas_extraidas = extrair_texto_pdf(conteudo_buffer)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar o arquivo PDF: {str(e)}")

    print(paginas_extraidas)
    if not paginas_extraidas:
        raise HTTPException(status_code=400, detail="Falha na extração do texto do contrato.")

    # Etapa 2: limpar texto (se aplicável)

    try:
        # Etapa 3: extrai dados
        dados_extraidos = extrair_dados_contrato(paginas_extraidas)

        # Etapa 4: valida os dados extraídos
        dados_validados = validar_extracao(dados_extraidos, paginas_extraidas)

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return dados_validados
