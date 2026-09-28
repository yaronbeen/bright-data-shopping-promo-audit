"""Compare Shopping result placement for one merchant across chosen queries."""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

SHOPPING_DATASET_ID = "gd_m31f2k0d2m1bah4f3b"


def _domain(value):
    value = value.strip().lower()
    if "://" not in value:
        value = "//" + value
    value = (urlparse(value).hostname or "").removeprefix("www.").rstrip(".")
    if not value or " " in value or "." not in value:
        raise ValueError("Provide a merchant domain such as shop.example")
    return value


def summarize_visibility(rows, merchant_domain):
    target = _domain(merchant_domain)
    queries = {}
    products = {}

    def matches_target(row):
        merchant = row.get("merchant") or ""
        candidate = merchant if "://" in merchant or "." in merchant else row.get("product_url") or ""
        try:
            host = _domain(candidate)
            return host == target or host.endswith("." + target)
        except ValueError:
            return False

    for row in rows:
        query = row.get("query") or "unknown"
        if matches_target(row):
            try:
                position = int(row["position"])
                if position < 1:
                    position = None
            except (KeyError, TypeError, ValueError):
                position = None
            current = queries.setdefault(query, None)
            if position is not None and (current is None or position < current):
                queries[query] = position
            products.setdefault(query, []).append({
                "position": position,
                "title": row.get("title"),
                "product_url": row.get("product_url"),
                "price": row.get("price"),
                "currency": row.get("currency"),
            })
        else:
            queries.setdefault(query, None)
    count = sum(any(matches_target(row) for row in rows if (row.get("query") or "unknown") == query) for query in queries)
    return {"query_count": len(queries), "queries_with_merchant": count, "presence_rate": round(count / len(queries), 3) if queries else 0, "best_rank_by_query": dict(sorted(queries.items())), "evidence_by_query": dict(sorted(products.items())), "decision_note": "Presence and rank describe only returned Shopping results for these queries; they are not sales, impression share, or ad attribution."}


def collect_shopping(query, api_key):
    url = "https://www.google.com/search?tbm=shop&q=" + quote_plus(query)
    body = json.dumps({"input": [{"url": url}]}).encode()
    request = Request(f"https://api.brightdata.com/datasets/v3/scrape?dataset_id={SHOPPING_DATASET_ID}&format=json", data=body, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urlopen(request, timeout=65) as response:
        if getattr(response, "status", 200) == 202:
            raise RuntimeError("Bright Data returned an async snapshot; use the documented async workflow")
        return json.load(response)


def emit_cli_error(error):
    status = error.code if isinstance(error, HTTPError) else None
    print(json.dumps({"error": {"code": "http_error" if status else "network_error", "message": f"Shopping collection failed{f' with HTTP {status}' if status else ''}; no automatic retry was attempted.", "retryable": False}}), file=sys.stderr)
    raise SystemExit(1)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python3 tool.py SAMPLE.json MERCHANT_DOMAIN | --live QUERY MERCHANT_DOMAIN")
    if sys.argv[1] == "--live":
        if len(sys.argv) != 4 or not os.getenv("BRIGHT_DATA_API_KEY"):
            raise SystemExit("Set BRIGHT_DATA_API_KEY and provide a query plus merchant domain")
        try:
            rows = collect_shopping(sys.argv[2], os.environ["BRIGHT_DATA_API_KEY"])
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as error:
            emit_cli_error(error)
        result = summarize_visibility(rows, sys.argv[3])
    else:
        with open(sys.argv[1], encoding="utf-8") as source:
            rows = json.load(source)
        result = summarize_visibility(rows, sys.argv[2])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
