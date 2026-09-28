import unittest
from io import BytesIO
from unittest.mock import patch

from tool import summarize_visibility


class ShoppingPromoAuditTests(unittest.TestCase):
    def test_summarizes_merchant_presence_and_best_observed_rank(self):
        rows = [
            {"query": "desk lamp", "merchant": "Shop Example", "product_url": "https://shop.example/lamp", "position": 4},
            {"query": "lamp sale", "merchant": "other.example", "position": 1},
            {"query": "lamp sale", "merchant": "Shop Example", "product_url": "https://shop.example/lamp", "position": 2},
        ]
        result = summarize_visibility(rows, "shop.example")
        self.assertEqual(result["query_count"], 2)
        self.assertEqual(result["queries_with_merchant"], 2)
        self.assertEqual(result["presence_rate"], 1.0)
        self.assertEqual(result["best_rank_by_query"]["lamp sale"], 2)
        self.assertEqual(result["evidence_by_query"]["lamp sale"][0]["product_url"], "https://shop.example/lamp")

    def test_missing_rank_is_not_inferred_and_domain_is_normalized(self):
        result = summarize_visibility([{"query": "x", "merchant": "SHOP.example", "product_url": "https://shop.example/path"}], "shop.example")
        self.assertIsNone(result["best_rank_by_query"]["x"])

    def test_rejects_invalid_domain(self):
        with self.assertRaises(ValueError):
            summarize_visibility([], "bad domain")

    def test_url_inputs_normalize_host_strip_port_and_require_exact_or_subdomain_match(self):
        rows = [
            {"query": "x", "merchant": "https://www.shop.example:8443/path?q=1", "position": 2},
            {"query": "y", "product_url": "https://sub.shop.example/product", "position": 3},
            {"query": "z", "product_url": "https://notshop.example/product", "position": 1},
        ]
        result = summarize_visibility(rows, "https://shop.example:443/?campaign=1")
        self.assertEqual(result["queries_with_merchant"], 2)

    def test_live_collection_uses_documented_shopping_dataset_and_url_input(self):
        from tool import collect_shopping
        response = BytesIO(b'[]')
        with patch("tool.urlopen", return_value=response) as mocked:
            collect_shopping("desk lamp", "test-key")
        request = mocked.call_args.args[0]
        self.assertIn("dataset_id=gd_m31f2k0d2m1bah4f3b", request.full_url)
        self.assertIn(b"tbm=shop", request.data)

    def test_live_cli_errors_are_structured_nonretryable_and_secret_safe(self):
        import json
        import os
        from contextlib import redirect_stderr
        from io import StringIO
        from urllib.error import URLError
        from tool import main
        with patch("tool.collect_shopping", side_effect=URLError("secret-token")), patch.dict(os.environ, {"BRIGHT_DATA_API_KEY": "secret-token"}), patch("sys.argv", ["tool.py", "--live", "query", "shop.example"]), redirect_stderr(StringIO()) as error:
            with self.assertRaises(SystemExit) as exit_error:
                main()
        payload = json.loads(error.getvalue())
        self.assertEqual(exit_error.exception.code, 1)
        self.assertFalse(payload["error"]["retryable"])
        self.assertNotIn("secret-token", error.getvalue())


if __name__ == "__main__":
    unittest.main()
