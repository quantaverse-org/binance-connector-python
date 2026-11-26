import hmac
import io
import json
import os
import runpy
import sys
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qsl

import requests


SCRIPTS = Path(__file__).resolve().parents[1]


class MarginSpecialKeyCliTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(sys, "path", [str(SCRIPTS), *sys.path]))
        stack.enter_context(patch("_binance_cli.load_dotenv"))
        credentials = {
            "BINANCE_MASTER_API_KEY": "caller-key",
            "BINANCE_MASTER_API_SECRET": "caller-secret",
        }
        stack.enter_context(patch.dict(os.environ, credentials, clear=True))
        self.request = stack.enter_context(patch("requests.sessions.Session.request"))
        self.output = stack.enter_context(redirect_stdout(io.StringIO()))
        stack.enter_context(redirect_stderr(io.StringIO()))

    def invoke(self, script, args, body=b"", status=200):
        response = requests.Response()
        response.status_code = status
        response._content = body
        self.request.return_value = response
        with patch.object(sys, "argv", [script, *args]):
            runpy.run_path(str(SCRIPTS / script), run_name="__main__")

    def check_request(self, method, path, params):
        self.request.assert_called_once()
        request = self.request.call_args.kwargs
        self.assertEqual(request["method"].upper(), method)
        self.assertEqual(request["url"], "https://api.binance.com/sapi/v1/margin/" + path)
        self.assertEqual(request["headers"]["X-MBX-APIKEY"], "caller-key")
        unsigned, signature = request["params"].rsplit("&signature=", 1)
        expected = hmac.digest(b"caller-secret", unsigned.encode(), "sha256").hex()
        self.assertEqual(signature, expected)
        query = dict(parse_qsl(unsigned))
        self.assertGreater(int(query.pop("timestamp")), 0)
        self.assertEqual(query, params)

    def test_query_cross_margin(self):
        result = [{"apiKey": "example-key", "apiName": "example"}]
        self.invoke("query_special_key_list.py", [], json.dumps(result).encode())
        self.check_request("GET", "api-key-list", {})
        self.assertEqual(json.loads(self.output.getvalue()), result)

    def test_query_isolated_margin(self):
        self.invoke(
            "query_special_key_list.py", ["--symbol", "ETHUSDT", "--recv-window", "9000"],
            b"[]",
        )
        self.check_request("GET", "api-key-list", {"symbol": "ETHUSDT", "recvWindow": "9000"})

    def test_delete_isolated_margin(self):
        self.invoke("delete_special_key.py", [
            "--api-key", "target-key", "--symbol", "BTCUSDT", "--recv-window", "5000"
        ])
        self.check_request("DELETE", "apiKey", {
            "apiKey": "target-key", "symbol": "BTCUSDT", "recvWindow": "5000"
        })

    def test_delete_requires_target(self):
        with self.assertRaises(SystemExit) as error:
            self.invoke("delete_special_key.py", [])
        self.assertEqual(error.exception.code, 2)
        self.request.assert_not_called()

    def test_http_error(self):
        with self.assertRaises(SystemExit) as error:
            self.invoke(
                "delete_special_key.py", ["--api-key", "target-key"],
                b'{"code": -2015, "msg": "Invalid API key"}', status=401,
            )
        self.assertNotEqual(error.exception.code, 0)
        self.check_request("DELETE", "apiKey", {"apiKey": "target-key"})
