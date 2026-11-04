import unittest
from unittest.mock import patch  # 在 with 作用域内临时替换依赖
from httpx2 import Request  # 当前 SDK 所用 HTTP 库
from openai import APITimeoutError  # 使用已安装 SDK 的真实异常类型
from model_client import ask_once, ModelCallError  # 被测函数和期望的项目异常
from httpx2 import Request, Response
from openai import APITimeoutError, AuthenticationError, APIConnectionError
from types import SimpleNamespace
import os

class ModelClientTests(unittest.TestCase):  # 组织测试与断言
    def test_timeout_is_classified(self):  # test_ 前缀让测试框架识别用例
        settings = {  # 测试配置
            "api_key": "unit-test-placeholder",
            "base_url": "https://example.invalid",
            "model": "unit-test-model",
        }
        request = Request("POST", "https://example.invalid/chat/completions")
        with patch("model_client.load_settings", return_value=settings): # 在原代码读取配置信息时将其替换为测试用的测试配置
            with patch("model_client.OpenAI") as factory:
                client = factory.return_value.__enter__.return_value
                client.chat.completions.create.side_effect = APITimeoutError(request=request)
                with self.assertRaises(ModelCallError) as caught:
                    ask_once("解释一下 API")
                self.assertEqual(caught.exception.kind, "timeout")
                client.chat.completions.create.assert_called_once()

    def test_auth_is_classified(self):
        settings = {
            "api_key": "unit-test-placeholder",
            "base_url": "https://example.invalid",
            "model": "unit-test-model",
        }
        request = Request("POST", "https://example.invalid/chat/completions")
        response = Response(401, request=request)  # 构造错误响应对象，不发送请求
        error = AuthenticationError(  # 模拟 SDK 报告认证失败
            "simulated authentication failure",
            response=response,
            body=None,
        )

        with patch("model_client.load_settings", return_value=settings):
            with patch("model_client.OpenAI") as factory:
                client = factory.return_value.__enter__.return_value
                client.chat.completions.create.side_effect = error

                with self.assertRaises(ModelCallError) as caught:
                    ask_once("解释一下 API")

                self.assertEqual(caught.exception.kind, "auth")
                client.chat.completions.create.assert_called_once()

    def test_connection_is_classified(self):
        settings = {
            "api_key": "unit-test-placeholder",
            "base_url": "https://example.invalid",
            "model": "unit-test-model",
        }
        request = Request("POST", "https://example.invalid/chat/completions")
        with patch("model_client.load_settings", return_value=settings):  # 在原代码读取配置信息时将其替换为测试用的测试配置
            with patch("model_client.OpenAI") as factory:
                client = factory.return_value.__enter__.return_value
                client.chat.completions.create.side_effect = APIConnectionError(request=request)
                with self.assertRaises(ModelCallError) as caught:
                    ask_once("解释一下 API")
                self.assertEqual(caught.exception.kind, "connection")
                client.chat.completions.create.assert_called_once()

    def test_blank_content_is_rejected(self):
        settings = {
            "api_key": "unit-test-placeholder",
            "base_url": "https://example.invalid",
            "model": "unit-test-model",
        }
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(content="   "),
                )
            ]
        )
        with patch("model_client.load_settings", return_value=settings):
            with patch("model_client.OpenAI") as factory:
                client = factory.return_value.__enter__.return_value
                client.chat.completions.create.return_value = response
                with self.assertRaises(ModelCallError) as caught:
                    ask_once("解释一下 API")
                self.assertEqual(caught.exception.kind, "invalid_response")
                client.chat.completions.create.assert_called_once()

    def test_empty_choices_is_rejected(self):
        settings = {
            "api_key": "unit-test-placeholder",
            "base_url": "https://example.invalid",
            "model": "unit-test-model",
        }
        response = SimpleNamespace(
            choices=[]
        )
        with patch("model_client.load_settings", return_value=settings):
            with patch("model_client.OpenAI") as factory:
                client = factory.return_value.__enter__.return_value
                client.chat.completions.create.return_value = response
                with self.assertRaises(ModelCallError) as caught:
                    ask_once("解释一下 API")
                self.assertEqual(caught.exception.kind, "invalid_response")
                client.chat.completions.create.assert_called_once()

    def test_unfinished_response_is_rejected(self):
        settings = {
            "api_key": "unit-test-placeholder",
            "base_url": "https://example.invalid",
            "model": "unit-test-model",
        }
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="length",
                    message=SimpleNamespace(content="  API 用于软件之间通信。\n"),
                )
            ]
        )
        with patch("model_client.load_settings", return_value=settings):
            with patch("model_client.OpenAI") as factory:
                client = factory.return_value.__enter__.return_value
                client.chat.completions.create.return_value = response
                with self.assertRaises(ModelCallError) as caught:
                    ask_once("解释一下 API")
                self.assertEqual(caught.exception.kind, "invalid_response")
                client.chat.completions.create.assert_called_once()

    def test_valid_response_returns_text(self):
        settings = {
            "api_key": "unit-test-placeholder",
            "base_url": "https://example.invalid",
            "model": "unit-test-model",
        }
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(content="  API 用于软件之间通信。\n"),
                )
            ]
        )

        with patch("model_client.load_settings", return_value=settings):
            with patch("model_client.OpenAI") as factory:
                client = factory.return_value.__enter__.return_value
                client.chat.completions.create.return_value = response

                answer = ask_once("解释一下 API", max_tokens=256)
                self.assertEqual(answer, "API 用于软件之间通信。")

                create_mock = client.chat.completions.create
                create_mock.assert_called_once()
                actual_max_tokens = create_mock.call_args.kwargs["max_tokens"]
                self.assertEqual(actual_max_tokens, 256)

    def test_blank_question_is_rejected_before_dependencies(self):
        with patch("model_client.load_settings") as loader:
            with patch("model_client.OpenAI") as factory:
                with self.assertRaisesRegex(ValueError, "question cannot be empty"):
                    ask_once(" \t\n")
                loader.assert_not_called()
                factory.assert_not_called()

    def test_missing_key_is_rejected_before_client(self):
        env = {
            "DEEPSEEK_BASE_URL": "https://example.invalid",
            "DEEPSEEK_MODEL": "unit-test-model",
        }

        with patch.dict(os.environ, env, clear=True):
            with patch("config.load_dotenv"):
                with patch("model_client.OpenAI") as factory:
                    with self.assertRaisesRegex(ValueError, "DEEPSEEK_API_KEY"):
                        ask_once("解释一下 API")
                    factory.assert_not_called()

if __name__ == "__main__":
    unittest.main()
