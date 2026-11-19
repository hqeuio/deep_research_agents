import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch

from cli import main
from model_client import ModelCallError

class CLITests(unittest.TestCase):
    def test_main_uses_supplied_arguments(self):
        output = StringIO()

        with patch("cli.run_agent", return_value="测试回答") as ask:
            with redirect_stdout(output):
                code = main(["测试问题"])

            ask.assert_called_once_with("测试问题")
            self.assertEqual(code, 0)
            self.assertEqual(output.getvalue(), "测试回答\n")
    # 测试模型调用失败后是否会把错误说明当成正常回答
    # stderr 包含错误类别与相应的文字说明
    def test_model_error_goes_to_stderr(self):
        output = StringIO()  # 收集正常回答
        errors = StringIO()  # 收集错误诊断
        error = ModelCallError("timeout", "模型请求超时")

        with patch("cli.run_agent", side_effect=error) as ask:
            with redirect_stdout(output), redirect_stderr(errors):
                code = main(["测试问题"])

            self.assertEqual(code, 1)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("[timeout]", errors.getvalue())
            self.assertIn("模型请求超时", errors.getvalue())
            ask.assert_called_once_with("测试问题")

    def test_input_or_config_error_goes_to_stderr(self):
        output = StringIO()
        errors = StringIO()
        error = ValueError("DEEPSEEK_API_KEY is missing or empty")
        with patch("cli.run_agent", side_effect=error) as ask:
            with redirect_stdout(output), redirect_stderr(errors):
                code = main(["测试问题"])
            self.assertEqual(code, 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("输入或配置错误", errors.getvalue())
            self.assertIn("DEEPSEEK_API_KEY", errors.getvalue())
            ask.assert_called_once_with("测试问题")
    def test_blank_question_is_rejected_before_model_request(self):
        stdout = StringIO()
        stderr = StringIO()

        with patch("agent_graph.request_turn") as request:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main([" \t\n"])

        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("question cannot be empty", stderr.getvalue())
        request.assert_not_called()

if __name__ == "__main__":
    unittest.main()
