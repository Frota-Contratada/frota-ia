import os
import mimetypes
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse

leitor_router = APIRouter(prefix="/contratos", tags=["Leitura"])

from services.database import (
    parse_date,
    insert_contrato_db,
    get_contrato_mais_recente_ativo_db,
)

# Diretório base para armazenamento dos contratos
UPLOAD_DIR = r"C:\Contratos"


def ensure_upload_dir():
    r"""Garante que a pasta C:\Contratos exista no sistema."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


@leitor_router.on_event("startup")
def startup_event():
    ensure_upload_dir()


@leitor_router.post("/upload", summary="Receber, armazenar arquivo e registrar contrato no banco de dados")
async def upload_contrato(
    filial: int = Form(..., description="Código da filial (DECIMAL(10,0))"),
    fornecedor: int = Form(..., description="Código do fornecedor (DECIMAL(10,0))"),
    nCdUsuarioCadastro: int = Form(..., description="Código do usuário de cadastro (DECIMAL(10,0))"),
    dVigenciaInicio: str = Form(..., description="Data de início da vigência (YYYY-MM-DD ou DD-MM-YYYY)"),
    dVigenciaFim: Optional[str] = Form(None, description="Data de fim da vigência (opcional, YYYY-MM-DD ou DD-MM-YYYY)"),
    file: UploadFile = File(..., description="Arquivo de contrato em buffer")
):
    """
    1. Salva o arquivo na pasta C:\\Contratos\\{filial} com o padrão: {fornecedor}_{dd-MM-yyyy}.ext
    2. Registra o contrato na tabela Contrato do SQL Server.
    3. Cria o vínculo na tabela FilialFornecedor.
    """
    ensure_upload_dir()

    # Valida as datas recebidas
    try:
        dt_inicio = parse_date(dVigenciaInicio)
        dt_fim = parse_date(dVigenciaFim) if dVigenciaFim else None
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    if dt_fim and dt_inicio and dt_fim < dt_inicio:
        raise HTTPException(
            status_code=400,
            detail="A data de fim da vigência não pode ser anterior à data de início."
        )

    # Cria a pasta da filial se não existir
    filial_dir = os.path.join(UPLOAD_DIR, str(filial))
    os.makedirs(filial_dir, exist_ok=True)

    # Formata a data atual em dd-MM-yyyy para o nome do arquivo
    today_str = datetime.now().strftime("%d-%m-%Y")

    # Extrai a extensão original do arquivo
    original_filename = file.filename or ""
    _, ext = os.path.splitext(original_filename)

    saved_filename = f"{fornecedor}_{today_str}{ext}"
    file_path = os.path.join(filial_dir, saved_filename)

    # 1. Grava o arquivo físico no disco
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar o arquivo físico: {str(e)}"
        )

    # 2. Grava os registros no SQL Server (Contrato e FilialFornecedor)
    try:
        nCdContrato = insert_contrato_db(
            filial=filial,
            fornecedor=fornecedor,
            caminho_arquivo=file_path,
            nCdUsuarioCadastro=nCdUsuarioCadastro,
            dVigenciaInicio=dt_inicio,
            dVigenciaFim=dt_fim
        )
    except Exception as e:
        # Se falhar no banco, remove o arquivo salvo para evitar lixo
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao registrar contrato no banco de dados: {str(e)}"
        )

    return {
        "message": "Contrato e arquivo armazenados com sucesso",
        "nCdContrato": nCdContrato,
        "filial": filial,
        "fornecedor": fornecedor,
        "nCdUsuarioCadastro": nCdUsuarioCadastro,
        "dVigenciaInicio": str(dt_inicio),
        "dVigenciaFim": str(dt_fim) if dt_fim else None,
        "filename": saved_filename,
        "path": file_path
    }


@leitor_router.get("/", summary="Devolver contrato mais recente ativo por filial e fornecedor")
async def download_contrato(
    filial: int = Query(..., description="Código da filial (DECIMAL(10,0))"),
    fornecedor: int = Query(..., description="Código do fornecedor (DECIMAL(10,0))")
):
    """
    Consulta no SQL Server o contrato mais recente ativo para a Filial e Fornecedor informados.
    Retorna o arquivo físico correspondente.
    """
    try:
        contrato = get_contrato_mais_recente_ativo_db(filial=filial, fornecedor=fornecedor)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar banco de dados: {str(e)}"
        )

    if not contrato:
        return JSONResponse(
            status_code=404,
            content={"message": f"Nenhum contrato ativo encontrado para Filial {filial} e Fornecedor {fornecedor}"}
        )

    file_path = contrato["cCaminhoArquivo"]

    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={"message": f"Arquivo físico não encontrado no caminho: {file_path}"}
        )

    matched_filename = os.path.basename(file_path)
    media_type, _ = mimetypes.guess_type(file_path)
    if not media_type:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=matched_filename,
        media_type=media_type
    )