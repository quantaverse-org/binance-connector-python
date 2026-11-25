import io
import json
import os
import sys
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qs

with patch.object(sys, "path", [str(Path(__file__).resolve().parents[1]), *sys.path]):
    import delete_sub_account_api_key
    import query_sub_account_api_key


class SubAccountCliTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch("_sub_account_cli.load_dotenv"))
        credentials = {
            "BINANCE_MASTER_API_KEY": "test-master",
            "BINANCE_MASTER_API_SECRET": "test-secret",
            "BINANCE_TARGET_SUB_API_KEY": "stale-key",
        }
        stack.enter_context(patch.dict(os.environ, credentials, clear=True))
        self.request = stack.enter_context(patch("requests.Session.request"))
        self.output = stack.enter_context(redirect_stdout(io.StringIO()))

    def call(self, script, args, response):
        self.request.return_value = Mock(
            status_code=200, headers={}, text=json.dumps(response)
        )
        with patch.object(sys, "argv", ["script", "--email", "sub@example.com", *args]):
            script.main()
        self.request.assert_called_once()
        kwargs = self.request.call_args.kwargs
        self.assertEqual(
            kwargs["url"], "https://api.binance.com/sapi/v1/sub-account/subAccountApi"
        )
        self.assertEqual(kwargs["headers"]["X-MBX-APIKEY"], "test-master")
        params = parse_qs(kwargs["params"])
        self.assertEqual(params["email"], ["sub@example.com"])
        self.assertIn("signature", params)
        self.assertIn("timestamp", params)
        return kwargs["method"], params

    def test_query_lists_page_ignoring_stale_target(self):
        response = {
            "total": 1, "rows": [{"apiName": "example", "apikey": "example-key"}]
        }
        method, params = self.call(
            query_sub_account_api_key, ["--page", "2", "--size", "10"], response
        )
        self.assertEqual(method, "GET")
        self.assertEqual((params["page"], params["size"]), (["2"], ["10"]))
        self.assertNotIn("subAccountApiKey", params)
        self.assertEqual(json.loads(self.output.getvalue()), response)

    def test_query_targets_explicit_key(self):
        method, params = self.call(
            query_sub_account_api_key,
            ["--sub-account-api-key", "chosen-key"],
            {"total": 0, "rows": []},
        )
        self.assertEqual(method, "GET")
        self.assertEqual(params["subAccountApiKey"], ["chosen-key"])

    def test_delete_targets_explicit_key(self):
        method, params = self.call(
            delete_sub_account_api_key, ["--sub-account-api-key", "chosen-key"], {}
        )
        self.assertEqual(method, "DELETE")
        self.assertEqual(params["subAccountApiKey"], ["chosen-key"])

    def test_delete_requires_explicit_target_despite_stale_environment(self):
        with self.assertRaises(SystemExit) as error, redirect_stderr(io.StringIO()):
            self.call(delete_sub_account_api_key, [], {})
        self.assertEqual(error.exception.code, 2)
        self.request.assert_not_called()
