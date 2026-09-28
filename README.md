# Bright Data Shopping Promotion Placement Audit

Check whether a merchant appears in returned Google Shopping product results for selected buyer queries, and record the best observed position. It helps an ecommerce marketer decide which query/product combinations need manual feed, availability, or campaign review. It is not an ad-attribution or sales report.

## Synthetic Example -> Decision

The invented fixture shows `northstar.example` in two of two query result sets, at positions 3 and 5. A marketer might inspect the lower-ranked query manually and check feed quality or campaign settings. The result does not prove impressions, paid placement, clicks, conversion, or a reason for rank.

## Workflow

1. Choose one bounded buyer query and the merchant domain to inspect.
2. Collect Google Shopping results for that query with the documented US dataset.
3. Match returned product URLs to the merchant domain and retain the best observed position.
4. Repeat manually for a small query list and decide what feed or campaign settings deserve inspection.

## Setup

Python 3.10+; standard library only.

```bash
cp .env.example .env
export BRIGHT_DATA_API_KEY="your-key"
```

The official [Google Scraper API docs](https://docs.brightdata.com/products/scrapers/google/introduction.md) list Google Shopping Products Search US dataset `gd_m31f2k0d2m1bah4f3b`. The [by-URL request reference](https://docs.brightdata.com/api-reference/scrapers/search-engines-apis/google-shopping-products-search-us-collect-by-url) documents input as `{ "input": [{"url":"https://www.google.com/search?tbm=shop&q=..."}] }` and fields including query, position, title, merchant, price, currency, rating, and product URL.

## Run

```bash
python3 tool.py sample.json northstar.example
BRIGHT_DATA_API_KEY="your-key" python3 tool.py --live "insulated water bottle" northstar.example
python3 -m unittest -v
```

One bounded query produces one live dataset scrape request; this may incur charges. Larger batch monitoring is out of scope. Merchant inputs are normalized as URL hostnames (ports, paths, and queries are ignored). A result matches the target when its host is exactly the target domain or a subdomain ending in `.` plus the target; unrelated suffixes do not match. When the merchant field is a human-readable label rather than a domain/URL, matching falls back to the product URL host. The programmatic function `summarize_visibility` supports offline records. Requests are not automatically retried because repeating a billable POST may duplicate usage.

## Outputs

JSON contains distinct query count, query count with a merchant result, observed presence rate, best observed rank by query, matched product URLs/titles, and explicit limitations. Missing ranks remain null; no rank is imputed.

On live HTTP/network/API failure, the CLI writes a JSON object to stderr with an `error` containing a stable `code`, sanitized `message`, and `retryable: false`, then exits 1. Success JSON remains on stdout. No automatic retry is made.

## Differentiation

The account already has general Google SERP scrapers, SEO/query maps, competitor pricing trackers, and a private Skiplagged flight-price monitor. This project uses the Shopping product-results surface for a narrow merchant-placement decision, not organic SEO opportunity synthesis or price history. Price, ratings, and review counts are deliberately not analyzed.

## FAQ

**Does position mean an ad was shown?** No. This dataset returns product results and position; this tool does not infer paid/organic status unless the source explicitly returns it.

**Does presence rate represent impression share?** No. It is presence in this bounded set of returned queries only.

**Can I run offline?** Yes, use the synthetic fixture and tests. Live calls require Bright Data API credentials.

## Compliance and limitations

Only query public Shopping results relevant to legitimate market analysis. Locale, time, device, and result composition affect observations. Check current Bright Data account pricing before a live call. Do not interpret this output as campaign attribution or a guaranteed rank.

## Bright Data

Powered by [Bright Data Google Shopping Scraper API](https://docs.brightdata.com/products/scrapers/google/introduction.md). MIT licensed.
