"""Real SDK/HTTP smoke tests; no external gateway call or payment."""
import os
import socket
import subprocess
import sys
import time
import unittest

import httpx


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.process = None
        cls.client = None
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        cls.key = 'protocol-test-only-not-a-deployment-secret-12345'
        env = dict(os.environ, VENNATTA_MCP_API_KEY=cls.key)
        cls.process = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'app.mcp_bridge:create_app',
             '--factory', '--host', '127.0.0.1', '--port', str(port), '--no-access-log'],
            env=env,
        )
        cls.addClassCleanup(cls.cleanup)
        cls.client = httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=10)
        for _ in range(100):
            if cls.process.poll() is not None:
                raise RuntimeError('Bridge process exited during startup')
            try:
                if cls.client.get('/mcp').status_code == 401:
                    return
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        raise RuntimeError('Bridge startup timed out')

    @classmethod
    def cleanup(cls):
        if cls.client is not None:
            cls.client.close()
        if cls.process is not None and cls.process.poll() is None:
            cls.process.terminate()
            try:
                cls.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.process.kill()
                cls.process.wait(timeout=5)

    def rpc(self, identifier, method, params=None):
        payload = {'jsonrpc': '2.0', 'id': identifier, 'method': method}
        if params is not None:
            payload['params'] = params
        response = self.client.post(
            '/mcp', json=payload,
            headers={'Authorization': f'Bearer {self.key}',
                     'Accept': 'application/json, text/event-stream',
                     'MCP-Protocol-Version': '2025-03-26'},
        )
        self.assertEqual(response.status_code, 200, response.text[:500])
        body = response.json()
        self.assertNotIn('error', body)
        return body['result']

    def test_unauthenticated_rpc_rejected(self):
        response = self.client.post('/mcp', json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'})
        self.assertEqual(response.status_code, 401)

    def test_initialize_list_and_status_call(self):
        result = self.rpc(1, 'initialize', {
            'protocolVersion': '2025-03-26',
            'capabilities': {},
            'clientInfo': {'name': 'vennatta-ci', 'version': '0.1.0'},
        })
        self.assertIn('serverInfo', result)
        result = self.rpc(2, 'tools/list')
        names = {tool['name'] for tool in result['tools']}
        self.assertEqual(names, {'get_gateway_health', 'get_seller_capabilities', 'get_bridge_status'})
        result = self.rpc(3, 'tools/call', {'name': 'get_bridge_status', 'arguments': {}})
        self.assertFalse(result.get('isError', False))
        import json
        content = [item['text'] for item in result['content'] if item['type'] == 'text']
        self.assertTrue(content)
        state = json.loads(content[0])
        self.assertEqual(state['mode'], 'read_only')
        self.assertFalse(state['can_sign'])
        self.assertFalse(state['can_trade'])


if __name__ == '__main__':
    unittest.main()
