"""Exercise real SDK validation with the deployed public Host header."""
import unittest

import test_mcp_protocol


class PublicHostTests(test_mcp_protocol.ProtocolTests):
    def test_public_hostname_initialize_and_call(self):
        previous = self.client.headers.get('Host')
        try:
            for host in ('vennatta-mcp-bridge.onrender.com',
                         'vennatta-mcp-bridge.onrender.com:443'):
                self.client.headers['Host'] = host
                self.test_initialize_list_and_status_call()
        finally:
            if previous is None:
                self.client.headers.pop('Host', None)
            else:
                self.client.headers['Host'] = previous

    def test_unrelated_hostname_is_rejected(self):
        response = self.client.post(
            '/mcp',
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'},
            headers={'Authorization': f'Bearer {self.key}',
                     'Host': 'unrelated.example',
                     'Accept': 'application/json, text/event-stream'},
        )
        self.assertEqual(response.status_code, 421)


if __name__ == '__main__':
    unittest.main()
