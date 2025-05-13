# Feature 3: Market Data Integration & Display

**Feature Goal:**
To provide users with a general overview of current market conditions by displaying key market indices (e.g., S&P 500, NASDAQ, Dow Jones) and potentially other relevant market data points like the VIX. This data should be fetched from a reliable external API, cached efficiently, and displayed prominently on the main dashboard, ensuring it is scalable and reliable for many users.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/market-data/`):**
    *   `GET /overview`:
        *   Request: Requires authenticated user.
        *   Response Schema: `MarketOverviewSchema` (e.g., `List[MarketIndexSchema]`, where each item has `name`, `symbol`, `current_value`, `change_value`, `percent_change`, `last_updated_at`).
*   **External API:** A third-party market data provider (e.g., Finnhub.io, MarketStack, IEX Cloud, Alpha Vantage). An API key will be required and must be managed securely.
*   **Internal Logic:** Background task system (e.g., Celery or ARQ) for periodically fetching and caching market data to minimize external API calls, improve response times, and stay within API provider rate limits.

**Detailed Feature Requirements:**

1.  **Data Scope & Sources:**
    *   Fetch data for major US market indices: S&P 500 (e.g., SPY or ^GSPC), NASDAQ Composite (e.g., QQQ or ^IXIC), Dow Jones Industrial Average (e.g., DIA or ^DJI).
    *   Fetch data for the CBOE Volatility Index (VIX).
    *   For each index/item: current market value, change value from previous close, percentage change from previous close.
    *   Data should be sourced from a reputable financial data provider via their API.
2.  **Secure API Key Management:**
    *   The API key for the external market data provider must be stored securely (e.g., in environment variables, or a secrets management service) and accessed only by the backend.
3.  **Efficient Data Fetching & Caching Strategy:**
    *   Implement a background task (e.g., using Celery/ARQ) to periodically fetch market data. The frequency should be configurable (e.g., every 1-5 minutes during US market hours, less frequently or paused outside market hours).
    *   Cache the fetched data on the backend (e.g., using Redis or an in-memory cache like `cachetools` with appropriate TTL). The cache TTL should be slightly shorter than the fetch interval to ensure fresh data is usually available.
    *   The `/overview` API endpoint should primarily serve data from this cache.
    *   If the cache is empty or stale and a live fetch is triggered by an API call (fallback), it should be rate-limited or managed to avoid overwhelming the external API.
4.  **Display on Dashboard:**
    *   The market overview data should be displayed clearly and concisely on the main user dashboard (Feature 4).
    *   Each index should show its name/symbol, current value, change value, and percentage change.
    *   Use clear visual cues for positive (e.g., green text/arrow up) and negative (e.g., red text/arrow down) changes.
    *   Display the `last_updated_at` timestamp for the data.
5.  **Error Handling & Resilience:**
    *   Gracefully handle errors from the external market data API (e.g., API key issues, rate limits exceeded, service unavailability, invalid symbols).
    *   If a fresh fetch fails, the API endpoint should serve stale data from the cache if available, clearly indicating that the data is not live (e.g., with an older `last_updated_at` timestamp).
    *   Implement logging for all market data fetching attempts, successes, and failures.
6.  **Scalability & Reliability:**
    *   The caching mechanism is key to ensuring the backend API can serve many users without hitting external API limits.
    *   The background task for fetching should be reliable and monitored.
7.  **Testing:**
    *   Unit tests for parsing API responses and formatting data.
    *   Integration tests for the caching mechanism and the background fetching task (mocking the external API).

**Detailed Implementation Guide:**

*   **Backend (FastAPI):**
    1.  **Market Data Service (`app/services/market_data_service.py`):**
        *   `async def get_market_overview_data() -> MarketOverviewSchema:`
            *   Attempts to retrieve data from the cache (e.g., Redis).
            *   If cache miss or data is significantly stale (beyond a reasonable threshold, even if TTL hasn't expired but background task might have failed), it could potentially trigger an on-demand fetch (though primary updates should be via background task).
            *   Formats data from cache (or fresh fetch) into `MarketOverviewSchema`.
        *   `async def fetch_and_cache_external_market_data() -> None:` (Called by background task)
            *   Constructs requests to the chosen external market data API for the required symbols (SPX, IXIC, DJI, VIX).
            *   Handles API responses, parses the data to extract current value, change, percent change.
            *   Updates the cache (e.g., Redis) with the new data and a `last_updated_at` timestamp. Key could be `market_overview`.
    2.  **Background Task (`app/background_tasks/market_data_tasks.py`):**
        *   `fetch_market_indices_task()`: Celery/ARQ task that calls `market_data_service.fetch_and_cache_external_market_data()`.
        *   This task should be scheduled to run periodically (e.g., using Celery Beat or ARQ scheduler).
    3.  **Caching Implementation (`app/core/cache.py` or direct Redis usage):**
        *   Functions to get/set data from/to Redis, handling serialization/deserialization (e.g., JSON).
        *   Define appropriate cache keys (e.g., `"market_indices_overview"`) and TTLs (e.g., 5 minutes).
    4.  **Configuration (`app/core/config.py`):**
        *   `EXTERNAL_MARKET_DATA_API_KEY`: Loaded from environment.
        *   `EXTERNAL_MARKET_DATA_API_BASE_URL`: For the chosen provider.
        *   `MARKET_INDEX_SYMBOLS`: List of symbols to fetch (e.g., ["^GSPC", "^IXIC", "^DJI", "^VIX"]).
        *   `REDIS_HOST`, `REDIS_PORT` (if using Redis).
    5.  **Schemas (`app/schemas/market_data.py`):**
        *   `MarketIndexSchema(BaseModel)`: `name: str`, `symbol: str`, `current_value: float`, `change_value: float`, `percent_change: float`, `last_updated_at: datetime`.
        *   `MarketOverviewSchema(BaseModel)`: `indices: List[MarketIndexSchema]`, `data_source_timestamp: Optional[datetime]` (timestamp from the provider if available, or when it was fetched by our service).
    6.  **API Endpoint (`app/api/v1/endpoints/market_data.py`):**
        *   Implement `GET /overview` endpoint. It calls `market_data_service.get_market_overview_data()`.
*   **Frontend (Next.js):**
    1.  **Market Overview Component (`src/components/dashboard/MarketOverview.tsx`):**
        *   Responsible for fetching data from the backend `/api/v1/market-data/overview` endpoint using a client-side data fetching hook (e.g., SWR or React Query for automatic refetching/caching on client, or a simple `useEffect` fetch).
        *   Displays the list of market indices using `MarketIndexSchema` data.
        *   Shows loading state while data is being fetched.
        *   Handles and displays error messages if data fetching fails.
        *   Formats numbers and percentages appropriately.
        *   Uses color-coding for positive/negative changes.
    2.  **API Service Call (`src/services/marketDataService.ts`):**
        *   `async function getMarketOverview(): Promise<MarketOverviewSchema>` that calls the backend API.

**Pseudocode Example (Background Task Fetching Logic):**

```python
# In app/services/market_data_service.py

async def fetch_and_cache_external_market_data():
    # Assume settings.MARKET_INDEX_SYMBOLS_MAP = {"^GSPC": "S&P 500", ...}
    # Assume settings.EXTERNAL_MARKET_DATA_API_PROVIDER = "finnhub" (example)

    fetched_indices_data = []
    api_key = settings.EXTERNAL_MARKET_DATA_API_KEY
    base_url = settings.EXTERNAL_MARKET_DATA_API_BASE_URL # e.g., "https://finnhub.io/api/v1"

    async with httpx.AsyncClient() as client:
        for symbol, name in settings.MARKET_INDEX_SYMBOLS_MAP.items():
            try:
                # Example for Finnhub quote endpoint
                # response = await client.get(f"{base_url}/quote?symbol={symbol}&token={api_key}")
                # response.raise_for_status()
                # quote_data = response.json() # c: current, d: change, dp: percent_change, t: timestamp

                # MOCKING API RESPONSE FOR EXAMPLE
                quote_data = {
                    "c": random.uniform(3000, 15000),
                    "d": random.uniform(-100, 100),
                    "dp": random.uniform(-2, 2),
                    "t": int(datetime.utcnow().timestamp())
                }
                # END MOCK

                index_data = MarketIndexSchema(
                    name=name,
                    symbol=symbol,
                    current_value=quote_data.get("c"),
                    change_value=quote_data.get("d"),
                    percent_change=quote_data.get("dp"),
                    last_updated_at=datetime.fromtimestamp(quote_data.get("t"))
                )
                fetched_indices_data.append(index_data)
            except Exception as e:
                # Log error: f"Failed to fetch market data for {symbol}: {e}"
                # Continue to next symbol or handle error as appropriate
                pass

    if fetched_indices_data:
        overview_data = MarketOverviewSchema(indices=fetched_indices_data, data_source_timestamp=datetime.utcnow())
        await cache.set("market_overview", overview_data.model_dump_json(), expire_seconds=300) # Cache for 5 mins
        # Log: "Market overview data updated and cached."
    else:
        # Log: "No market data fetched, cache not updated."
```
This feature provides crucial context to users about the overall market environment, enhancing their decision-making process when viewing their portfolio.
