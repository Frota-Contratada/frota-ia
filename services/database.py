import pyodbc
from datetime import datetime, date
from typing import Optional, Dict, Any
from app.config import Settings

# Carrega as variáveis do arquivo .env
settings = Settings()

def get_db_connection():
    """Retorna uma conexão aberta com o SQL Server."""
    conn_str = settings.connection_dbgfc
    return pyodbc.connect(conn_str)


def parse_date(date_val: Optional[str]) -> Optional[date]:
    """Converte strings de datas variadas (dd-MM-yyyy, yyyy-MM-dd, dd/MM/yyyy) para objeto date."""
    if not date_val:
        return None
    
    date_val = str(date_val).strip()
    if not date_val:
        return None

    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_val, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Formato de data inválido: '{date_val}'. Utilize YYYY-MM-DD ou DD-MM-YYYY.")


def insert_contrato_db(
    filial: int,
    fornecedor: int,
    caminho_arquivo: str,
    nCdUsuarioCadastro: int,
    dVigenciaInicio: date,
    dVigenciaFim: Optional[date]
) -> int:
    """
    Insere os registros nas tabelas Contrato e FilialFornecedor em uma única transação atômica.
    Retorna o nCdContrato gerado.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Gera o próximo nCdContrato com trava de atualização
        cursor.execute("SELECT COALESCE(MAX(nCdContrato), 0) + 1 FROM Contrato WITH (UPDLOCK, HOLDLOCK)")
        row = cursor.fetchone()
        next_contrato_id = int(row[0]) if row and row[0] is not None else 1

        # Insere na tabela Contrato
        insert_contrato_sql = """
            INSERT INTO Contrato (
                nCdContrato,
                cCaminhoArquivo,
                nCdUsuarioCadastro,
                dVigenciaInicio,
                dVigenciaFim,
                dAlteracao
            ) VALUES (?, ?, ?, ?, ?, GETDATE())
        """
        cursor.execute(
            insert_contrato_sql,
            (next_contrato_id, caminho_arquivo, nCdUsuarioCadastro, dVigenciaInicio, dVigenciaFim)
        )

        # Insere na tabela FilialFornecedor
        insert_ff_sql = """
            INSERT INTO FilialFornecedor (
                nCdFilial,
                nCdFornecedor,
                nCdContrato
            ) VALUES (?, ?, ?)
        """
        cursor.execute(
            insert_ff_sql,
            (filial, fornecedor, next_contrato_id)
        )

        conn.commit()
        return next_contrato_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def get_contrato_mais_recente_ativo_db(filial: int, fornecedor: int) -> Optional[Dict[str, Any]]:
    """
    Busca o contrato ativo mais recente para a Filial e Fornecedor informados.
    Critério de 'Ativo': dVigenciaInicio <= DataAtual e (dVigenciaFim IS NULL ou dVigenciaFim >= DataAtual).
    Ordenação: Mais recente por dVigenciaInicio DESC, dAlteracao DESC, nCdContrato DESC.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT TOP 1
                c.nCdContrato,
                c.cCaminhoArquivo,
                c.nCdUsuarioCadastro,
                c.dVigenciaInicio,
                c.dVigenciaFim,
                c.dAlteracao,
                ff.nCdFilial,
                ff.nCdFornecedor
            FROM FilialFornecedor ff WITH (NOLOCK)
            INNER JOIN Contrato c WITH (NOLOCK) ON ff.nCdContrato = c.nCdContrato
            WHERE ff.nCdFilial = ?
              AND ff.nCdFornecedor = ?
              AND c.dVigenciaInicio <= CAST(GETDATE() AS DATE)
              AND (c.dVigenciaFim IS NULL OR c.dVigenciaFim >= CAST(GETDATE() AS DATE))
            ORDER BY c.dVigenciaInicio DESC, c.dAlteracao DESC, c.nCdContrato DESC
        """
        cursor.execute(query, (filial, fornecedor))
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "nCdContrato": int(row[0]),
            "cCaminhoArquivo": row[1],
            "nCdUsuarioCadastro": int(row[2]),
            "dVigenciaInicio": row[3],
            "dVigenciaFim": row[4],
            "dAlteracao": row[5],
            "nCdFilial": int(row[6]),
            "nCdFornecedor": int(row[7])
        }
    finally:
        cursor.close()
        conn.close()
