import json
from pathlib import Path
from app.config import settings
from groq import Groq

caminho_prompt = Path(__file__).parent.parent / "prompts" / "validacao_prompt.txt"

def carregar_prompt(caminho_prompt: str):
    with open(caminho_prompt, "r", encoding="utf-8") as file:
        return file.read()


client = Groq(api_key=settings.require_groq_api_key())

def validar_extracao(dados_brutos: dict, texto_extraido: dict):
    template = carregar_prompt(caminho_prompt)
    json_extraido = json.dumps(dados_brutos, ensure_ascii=False, indent=2)
    texto_extraido = json.dumps(texto_extraido, ensure_ascii=False, indent=2)
    system_prompt = template.replace("{json_bruto}", json_extraido)

    try:
        print("[Validador] Enviando prompt para o validador...")
        resposta = client.chat.completions.create(
            model=settings.ai_validator_model,
            response_format={"type": "json_object"},
            reasoning_format="hidden",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": texto_extraido}
            ]
        )

        template_json = resposta.choices[0].message.content.strip()
        template_json = template_json.removeprefix("```json").removesuffix("```").strip()

        dados_validados = json.loads(template_json)

        return dados_validados

    except json.JSONDecodeError:
        dados_brutos["extracao"]["observacoes"].append(
            "Agente validador retornou formato inválido. Dados não revisados."
        )
        dados_brutos["extracao"]["confianca_geral"] = max(
            0.0, dados_brutos["extracao"].get("confianca_geral", 0.5) - 0.2
        )
        return dados_brutos

    except Exception as e:
        dados_brutos["extracao"]["observacoes"].append(
            f"Validação indisponível: {type(e).__name__}"
        )
        return dados_brutos
