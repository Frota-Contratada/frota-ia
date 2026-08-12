import json
from pathlib import Path
from google.genai import Client
from google.genai.types import GenerateContentConfig
from app.config import Settings

settings = Settings()
client = Client(api_key=settings.gemini_api_key)

caminho_prompt = Path(__file__).parent.parent / "prompts" / "extracao_prompt.txt"

def carregar_prompt(caminho_prompt: str):
    with open(caminho_prompt, "r", encoding="utf-8") as file:
        return file.read()

def extrair_dados_contrato(texto: str):
    template = carregar_prompt(caminho_prompt)
    texto = "\n\n".join(texto)
    system_prompt = template.replace("{texto_contrato}", texto)

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=system_prompt
        )
        template_json = response.text.strip()
        template_json = template_json.removeprefix("```json").removesuffix("```").strip()
        return json.loads(template_json)

    except json.JSONDecodeError:
        return {
            "extracao": {
                "status": "falha",
                "confianca_geral": 0.0,
                "observacoes": ["Gemini retornou resposta fora do formato JSON esperado"]
            },
            "fornecedor": None,
            "veiculo": [],
            "contrato": None,
            "modalidades": [],
            "regras": [],
        }
    except Exception as e:
        raise ValueError(f"Erro ao extrair dados do contrato: {e}")
