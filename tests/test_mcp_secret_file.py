import unittest
from unittest.mock import patch

from app.mcp_bridge import ApiKeyGate, load_api_key


class SecretFileTests(unittest.TestCase):
    @patch.dict('os.environ', {'VENNATTA_MCP_API_KEY': 'e' * 32}, clear=True)
    def test_environment_takes_precedence(self):
        with patch('app.mcp_bridge.Path.read_text') as read:
            self.assertEqual(load_api_key(), 'e' * 32)
            read.assert_not_called()

    @patch.dict('os.environ', {}, clear=True)
    def test_file_fallback(self):
        with patch('app.mcp_bridge.Path.read_text', return_value='f' * 32 + '\n'):
            self.assertEqual(load_api_key(), 'f' * 32)

    @patch.dict('os.environ', {}, clear=True)
    def test_missing_file_fails_closed(self):
        with patch('app.mcp_bridge.Path.read_text', side_effect=FileNotFoundError):
            with self.assertRaises(RuntimeError):
                ApiKeyGate(None, load_api_key())

    @patch.dict('os.environ', {}, clear=True)
    def test_short_file_fails_closed(self):
        with patch('app.mcp_bridge.Path.read_text', return_value='short'):
            with self.assertRaises(RuntimeError):
                ApiKeyGate(None, load_api_key())

    @patch.dict('os.environ', {}, clear=True)
    def test_unreadable_file_does_not_fall_back(self):
        with patch('app.mcp_bridge.Path.read_text', side_effect=PermissionError):
            with self.assertRaisesRegex(RuntimeError, '^Unable to load MCP secret file$'):
                load_api_key()


if __name__ == '__main__':
    unittest.main()
