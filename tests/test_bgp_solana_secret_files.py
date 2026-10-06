import unittest
from unittest.mock import Mock, patch

from app.solana_payments import _solana_setting


class SolanaSecretFileTests(unittest.TestCase):
    def read_setting(self, contents=None, error=None):
        file = Mock()
        if error is not None:
            file.read_text.side_effect = error
        else:
            file.read_text.return_value = contents
        root = Mock()
        root.__truediv__ = Mock(return_value=file)

        with patch.dict("os.environ", {}, clear=True):
            with patch("app.solana_payments.Path", return_value=root):
                result = _solana_setting("VENNATTA_SOLANA_ENABLED", "false")

        root.__truediv__.assert_called_once_with("VENNATTA_SOLANA_ENABLED")
        return result

    def test_plain_value(self):
        self.assertEqual(self.read_setting("true\n"), "true")

    def test_assignment_value(self):
        self.assertEqual(
            self.read_setting('VENNATTA_SOLANA_ENABLED="true"\n'),
            "true",
        )

    def test_missing_file_defaults_disabled(self):
        self.assertEqual(
            self.read_setting(error=FileNotFoundError()),
            "false",
        )

    def test_environment_takes_precedence(self):
        with patch.dict(
            "os.environ", {"VENNATTA_SOLANA_ENABLED": "false"}, clear=True
        ):
            with patch("app.solana_payments.Path") as path:
                self.assertEqual(
                    _solana_setting("VENNATTA_SOLANA_ENABLED", "false"),
                    "false",
                )
                path.assert_not_called()

    def test_empty_file_rejected(self):
        with self.assertRaises(RuntimeError):
            self.read_setting(" \n")

    def test_multiline_file_rejected(self):
        with self.assertRaises(RuntimeError):
            self.read_setting("true\nfalse")

    def test_unreadable_file_rejected(self):
        with self.assertRaises(PermissionError):
            self.read_setting(error=PermissionError())
