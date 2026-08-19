import json
from pathlib import Path
from app.config import settings
from groq import Groq
from services.database import get_tipos_veiculo, get_tipos_contrato

client = Groq(api_key=settings.groq_api_key)

caminho_prompt = Path(__file__).parent.parent / "prompts" / "extracao_prompt.txt"

def carregar_prompt(caminho_prompt: str):
    with open(caminho_prompt, "r", encoding="utf-8") as file:
        return file.read()

def extrair_dados_contrato(texto: list[str] | str):
    template = carregar_prompt(caminho_prompt)
    if isinstance(texto, list):
        texto = "\n\n".join(texto)

    tipos_veiculo = get_tipos_veiculo()
    tipos_contrato = get_tipos_contrato()

    system_prompt = (
        template
        .replace("{tipos_veiculo}", str(tipos_veiculo))
        .replace("{tipos_contrato}", str(tipos_contrato))
        .replace("{texto_contrato}", texto)
    )

    try:
        print("[Groq] Enviando prompt para o Groq...")
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                 }
            ]
        )
        template_json = response.choices[0].message.content.strip()
        template_json = template_json.removeprefix("```json").removesuffix("```").strip()
        return json.loads(template_json)

    except json.JSONDecodeError:
        return {
            "extracao": {
                "status": "falha",
                "confianca_geral": 0.0,
                "observacoes": ["Groq retornou resposta fora do formato JSON esperado"]
            },
            "fornecedor": None,
            "veiculo": [],
            "contrato": None,
            "modalidades": [],
            "regras": [],
        }
    except Exception as e:
        raise ValueError(f"Erro ao extrair dados do contrato: {e}")
