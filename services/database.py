import pyodbc
from typing import List
from app.config import settings

def get_db_connection():
    """Retorna uma conexão aberta com o SQL Server."""
    if not settings.connection_dbgfc:
        raise ValueError("A connection string CONNECTION_DBGFC não está configurada no .env.")
    return pyodbc.connect(settings.connection_dbgfc)

def get_tipos_veiculo() -> List[str]:
    """
    Busca os tipos de veículo cadastrados na tabela TipoVeiculo.
    Retorna uma lista de strings, ex: ['CARRO', 'MOTO', 'FURGÃO', 'CAMINHÃO', 'VAN'].
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cNmTpVeiculo FROM TipoVeiculo ORDER BY nCdTpVeiculo")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        tipos = [row[0].strip() for row in rows if row and row[0]]
        if tipos:
            return tipos
    except Exception as e:
        print(f"[Aviso] Falha ao consultar TipoVeiculo no banco de dados: {e}")

    # Fallback caso ocorra algum problema de conexão no ambiente
    return ['CARRO', 'MOTO', 'FURGÃO', 'CAMINHÃO', 'VAN']

def get_tipos_contrato() -> List[str]:
    """
    Busca os tipos de corrida/contrato cadastrados na tabela TipoCorrida.
    Retorna uma lista de strings, ex: ['PASSAGEIRO', 'DOCUMENTO', 'CARGA'].
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT cNmTipoCorrida FROM TipoCorrida ORDER BY nCdTipoCorrida")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        tipos = [row[0].strip().upper() for row in rows if row and row[0]]
        if tipos:
            return tipos
    except Exception as e:
        print(f"[Aviso] Falha ao consultar TipoCorrida no banco de dados: {e}")

    # Fallback caso ocorra algum problema de conexão no ambiente
    return ['PASSAGEIRO', 'DOCUMENTO', 'CARGA']
