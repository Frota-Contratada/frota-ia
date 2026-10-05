"""Contract checks for the two Groq stages and document-safe logging."""

import io
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("GROQ_API_KEY", "ci-placeholder")

from fastapi import UploadFile

from app.config import Settings
from routes import extracao as route
from services import extrator, validador


def completion(content, reasoning=None):
    return SimpleNamespace(choices=[SimpleNamespace(
        message=SimpleNamespace(content=content, reasoning=reasoning))])


class ModelConfigurationTests(unittest.TestCase):
    def test_defaults_and_environment_overrides(self):
        defaults = Settings(_env_file=None)
        self.assertEqual(defaults.ai_extract_model, "openai/gpt-oss-120b")
        self.assertEqual(defaults.ai_validator_model, "qwen/qwen3.8-27b")
        with patch.dict(os.environ, {"AI_EXTRACT_MODEL": "future-extract",
                                     "AI_VALIDATOR_MODEL": "future-validator"}):
            overridden = Settings(_env_file=None)
        self.assertEqual(overridden.ai_extract_model, "future-extract")
        self.assertEqual(overridden.ai_validator_model, "future-validator")

    def test_missing_groq_key_fails_clearly(self):
        settings = Settings(_env_file=None, groq_api_key=None)
        with self.assertRaisesRegex(ValueError, "GROQ_API_KEY is required"):
            settings.require_groq_api_key()


class GroqStageTests(unittest.TestCase):
    def test_extraction_uses_configured_model_and_json_mode(self):
        with patch.object(extrator.client.chat.completions, "create",
                          return_value=completion('{"extracao":{"status":"sucesso"}}')) as create, \
             patch.object(extrator, "get_tipos_veiculo", return_value=["CARRO"]), \
             patch.object(extrator, "get_tipos_contrato", return_value=["PASSAGEIRO"]):
            result = extrator.extrair_dados_contrato("Synthetic contract fixture")
        self.assertEqual(result["extracao"]["status"], "sucesso")
        self.assertEqual(create.call_args.kwargs["model"], "openai/gpt-oss-120b")
        self.assertEqual(create.call_args.kwargs["response_format"], {"type": "json_object"})
        self.assertEqual(create.call_args.kwargs["reasoning_format"], "hidden")

    def test_validator_preserves_contract_and_ignores_reasoning_field(self):
        source = {"extracao": {"confianca_geral": 0.8, "observacoes": []}}
        response = '{"extracao":{"confianca_geral":0.7,"observacoes":["Reviewed"]}}'
        with patch.object(validador.client.chat.completions, "create",
                          return_value=completion(response, reasoning="internal only")) as create:
            result = validador.validar_extracao(source, ["Synthetic contract fixture"])
        self.assertEqual(result["extracao"]["confianca_geral"], 0.7)
        self.assertEqual(create.call_args.kwargs["model"], "qwen/qwen3.8-27b")
        self.assertEqual(create.call_args.kwargs["response_format"], {"type": "json_object"})
        self.assertEqual(create.call_args.kwargs["reasoning_format"], "hidden")
        self.assertIn("Synthetic contract fixture", create.call_args.kwargs["messages"][1]["content"])

    def test_invalid_extraction_json_returns_existing_failure_shape(self):
        with patch.object(extrator.client.chat.completions, "create",
                          return_value=completion("not JSON")), \
             patch.object(extrator, "get_tipos_veiculo", return_value=[]), \
             patch.object(extrator, "get_tipos_contrato", return_value=[]):
            result = extrator.extrair_dados_contrato("Synthetic fixture")
        self.assertEqual(result["extracao"]["status"], "falha")
        self.assertEqual(result["regras"], [])

    def test_invalid_validator_json_keeps_original_and_lowers_confidence(self):
        source = {"extracao": {"confianca_geral": 0.8, "observacoes": []}}
        with patch.object(validador.client.chat.completions, "create",
                          return_value=completion("not JSON")):
            result = validador.validar_extracao(source, ["Synthetic fixture"])
        self.assertIs(result, source)
        self.assertAlmostEqual(result["extracao"]["confianca_geral"], 0.6)
        self.assertIn("Dados não revisados", result["extracao"]["observacoes"][0])

    def test_provider_error_and_timeout_follow_existing_paths(self):
        with patch.object(extrator.client.chat.completions, "create",
                          side_effect=RuntimeError("provider-secret-response")), \
             patch.object(extrator, "get_tipos_veiculo", return_value=[]), \
             patch.object(extrator, "get_tipos_contrato", return_value=[]):
            with self.assertRaisesRegex(ValueError, "Erro ao extrair dados do contrato") as raised:
                extrator.extrair_dados_contrato("Synthetic fixture")
        self.assertNotIn("provider-secret-response", str(raised.exception))
        source = {"extracao": {"confianca_geral": 0.8, "observacoes": []}}
        with patch.object(validador.client.chat.completions, "create",
                          side_effect=TimeoutError("timeout")):
            result = validador.validar_extracao(source, ["Synthetic fixture"])
        self.assertIs(result, source)
        self.assertIn("Validação indisponível", result["extracao"]["observacoes"][0])

    def test_no_operational_xai_dependency(self):
        root = Path(__file__).resolve().parents[1]
        for path in (root / "services" / "extrator.py",
                     root / "services" / "validador.py",
                     root / "requirements.txt"):
            self.assertNotIn("xai_sdk", path.read_text(encoding="utf-8"))
            self.assertNotIn("xai-sdk", path.read_text(encoding="utf-8"))


class DocumentLoggingTests(unittest.IsolatedAsyncioTestCase):
    async def test_route_does_not_log_extracted_pdf_text(self):
        marker = "SYNTHETIC_PRIVATE_PDF_TEXT"
        upload = UploadFile(filename="fixture.pdf", file=io.BytesIO(b"synthetic pdf"))
        with patch.object(route, "extrair_texto_pdf", return_value=[marker]), \
             patch.object(route, "extrair_dados_contrato", return_value={"extracao": {}}), \
             patch.object(route, "validar_extracao", return_value={"extracao": {}}), \
             self.assertLogs(route.logger, level="INFO") as captured:
            await route.extrair_texto(upload)
        self.assertNotIn(marker, "\n".join(captured.output))
        self.assertIn("pages=1", "\n".join(captured.output))


if __name__ == "__main__":
    unittest.main()
