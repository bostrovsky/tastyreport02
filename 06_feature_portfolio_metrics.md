# Feature 6: Portfolio Metrics Calculation & Display

**Feature Goal:**
To calculate, store, and display key portfolio-level risk metrics (e.g., Delta, Gamma, Theta, Vega) and other important summary statistics (e.g., Net Liquidity, Buying Power, Open Positions Count). These metrics provide users with insights into their overall portfolio risk exposure and status, supporting informed decision-making. The system must be scalable and reliable.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/reports/` or `/api/v1/portfolio/`):**
    *   `GET /metrics/current/{account_id}`:
        *   Request: Auth user, `account_id`.
        *   Response Schema: `PortfolioMetricsSchema` (e.g., `net_liquidity`, `buying_power`, `portfolio_delta`, `portfolio_gamma`, `portfolio_theta`, `portfolio_vega`, `open_positions_count`, `last_updated_at`).
    *   `GET /metrics/historical/{account_id}`: (Future Enhancement)
        *   Request: Auth user, `account_id`. Query params: `date` or `period`.
        *   Response Schema: `List[HistoricalPortfolioMetricsSchema]` (snapshot of metrics over time).

**Detailed Feature Requirements:**

1.  **Key Metrics Calculation:**
    *   **Net Liquidity (NL):** Current total value of the account (cash + market value of all positions). Should match broker if possible.
    *   **Buying Power:** Available funds for new trades (options buying power, stock buying power if distinguishable).
    *   **Portfolio Greeks (for options-heavy portfolios):**
        *   **Delta:** Sum of (individual position delta * position quantity * option multiplier).
        *   **Gamma:** Sum of (individual position gamma * position quantity * option multiplier).
        *   **Theta:** Sum of (individual position theta * position quantity * option multiplier).
        *   **Vega:** Sum of (individual position vega * position quantity * option multiplier).
    *   **Open Positions Count:** Total number of unique open positions.
    *   **Margin Requirements (Optional MVP):** Initial and maintenance margin if available from API.
2.  **Data Sources for Metrics:**
    *   **Net Liquidity, Buying Power:** Directly from TastyTrade account balances API (synced via Feature 2).
    *   **Position Greeks (Delta, Gamma, Theta, Vega):**
        *   Ideally, fetched directly from TastyTrade API per position if available and current.
        *   If not directly available or not fresh, they might need to be calculated using an option pricing model (e.g., Black-Scholes) with current underlying prices, volatility, interest rates, and time to expiration. This is complex and adds significant dependencies (market data for all underlyings, volatility surfaces, interest rates).
        *   **MVP Approach:** Prioritize using Greeks provided by TastyTrade API during position sync (Feature 2). If unavailable, these specific portfolio greeks might be deferred or shown as "N/A".
    *   **Open Positions Count:** Derived from synced position data.
3.  **Aggregation & Display:**
    *   Metrics should be aggregated at the overall portfolio level for a selected TastyTrade account.
    *   Display these metrics clearly on the Dashboard (Feature 4) and potentially in a dedicated portfolio summary view.
4.  **Data Freshness & Updates:**
    *   Net Liquidity and Buying Power should reflect the latest synced balance data.
    *   Portfolio Greeks and open positions count should reflect the latest synced position data.
    *   Clearly indicate the `last_updated_at` timestamp for these metrics.
5.  **Historical Tracking (Future Enhancement):**
    *   Store snapshots of key portfolio metrics daily to allow users to track trends over time.
6.  **Accuracy:**
    *   Metrics derived directly from the broker (NL, BP) should be accurate to the broker's reporting.
    *   Calculated Greeks depend on the accuracy of input data and models used.
7.  **Performance:**
    *   Fetching and aggregating metrics should be efficient.
    *   If calculations are intensive (e.g., custom Greek calculations), they might be done as part of the data sync background task (Feature 2) and stored with position data, rather than on-the-fly for API requests.
8.  **Testing:**
    *   Unit tests for any aggregation logic (e.g., summing up position deltas).
    *   Integration tests for API endpoints serving portfolio metrics.
    *   If custom Greek calculations are implemented, extensive testing of the option pricing model is required.

**Detailed Implementation Guide:**

*   **Backend (FastAPI):**
    1.  **Portfolio Metrics Service (`app/services/portfolio_metrics_service.py` - new, or extend `reporting_service.py`):**
        *   `async def get_current_portfolio_metrics(db: Session, account_id: int) -> PortfolioMetricsSchema:`
            *   Fetch latest `AccountBalanceSnapshot` for NL, BP.
            *   Fetch all current `Position` records for the account.
            *   Sum up Greeks (delta, gamma, theta, vega) from these position records (assuming Greeks are stored with position data from sync).
            *   Count open positions.
            *   Assemble into `PortfolioMetricsSchema`.
    2.  **Data Storage (Enhancements to existing models from Feature 2):**
        *   `Position` model (`db/models/position.py`): Ensure it has fields for `delta`, `gamma`, `theta`, `vega`, `current_market_value`. These should be populated during the TastyTrade data sync (Feature 2) if the API provides them.
        *   `AccountBalanceSnapshot` model (`db/models/account_balance.py` - or similar): Stores `net_liquidity`, `buying_power`, `timestamp` from sync.
    3.  **CRUD Operations:**
        *   `crud_position.py`: Method to fetch all active positions for an account.
        *   `crud_account_balance.py`: Method to fetch the latest balance snapshot.
    4.  **Schemas (`app/schemas/portfolio.py` or `app/schemas/report.py`):**
        *   `PortfolioMetricsSchema(BaseModel)`: `net_liquidity: float`, `buying_power: float`, `options_buying_power: Optional[float]`, `portfolio_delta: Optional[float]`, `portfolio_gamma: Optional[float]`, `portfolio_theta: Optional[float]`, `portfolio_vega: Optional[float]`, `open_positions_count: int`, `last_updated_at: datetime`.
    5.  **API Endpoint (`app/api/v1/endpoints/reports.py` or a new `portfolio.py`):**
        *   Implement `GET /metrics/current/{account_id}` endpoint, calling `portfolio_metrics_service.get_current_portfolio_metrics()`.
    6.  **Integration with Data Sync (Feature 2):**
        *   The data sync process is responsible for populating the `Position` records with Greek values and `AccountBalanceSnapshot` with NL/BP. If TastyTrade API doesn't provide Greeks directly for all positions, this is where a fallback calculation (if implemented) would occur, or they would be left null.
*   **Frontend (Next.js):**
    1.  **Display Components (Primarily in Dashboard - Feature 4):**
        *   Widgets or sections on the dashboard to display Net Liquidity, Buying Power, Portfolio Greeks, and Open Positions Count.
        *   These components will receive data from the `/metrics/current/{account_id}` API call.
    2.  **API Service Call (`src/services/reportService.ts` or `portfolioService.ts`):**
        *   Function `getCurrentPortfolioMetrics(accountId: string): Promise<PortfolioMetricsSchema>`.

**Pseudocode Example (Portfolio Metrics Service):**

```python
# In app/services/portfolio_metrics_service.py

from app.crud import crud_position, crud_account_balance
from app.schemas.portfolio import PortfolioMetricsSchema # Assuming this schema exists

class PortfolioMetricsService:
    def __init__(self, db: Session):
        self.db = db

    async def get_current_portfolio_metrics(self, tastytrade_db_account_id: int) -> PortfolioMetricsSchema:
        # Fetch latest balance snapshot
        latest_balance = await crud_account_balance.get_latest_for_account(self.db, account_id=tastytrade_db_account_id)
        net_liquidity = latest_balance.net_liquidity if latest_balance else 0.0
        buying_power = latest_balance.buying_power if latest_balance else 0.0
        balance_last_updated = latest_balance.timestamp if latest_balance else datetime.min

        # Fetch all open positions for the account
        open_positions = await crud_position.get_open_positions_for_account(self.db, account_id=tastytrade_db_account_id)

        portfolio_delta = 0.0
        portfolio_gamma = 0.0
        portfolio_theta = 0.0
        portfolio_vega = 0.0
        open_positions_count = len(open_positions)
        position_data_last_updated = datetime.min

        if open_positions:
            position_data_last_updated = max(p.last_updated_at for p in open_positions if p.last_updated_at)
                                           if any(p.last_updated_at for p in open_positions) else datetime.min

            for pos in open_positions:
                # Assuming position quantity includes direction (e.g., -100 for short)
                # And option multiplier is handled (e.g., 100 for standard US options)
                # Greeks should be per share, so multiply by quantity and multiplier
                multiplier = pos.instrument_multiplier or 100 # Default for options
                if pos.delta is not None:
                    portfolio_delta += pos.delta * pos.quantity * (1 if pos.instrument_type != "OPTION" else multiplier)
                if pos.gamma is not None:
                    portfolio_gamma += pos.gamma * pos.quantity * (1 if pos.instrument_type != "OPTION" else multiplier)
                if pos.theta is not None:
                    # Theta is often displayed as daily decay, ensure sign convention is consistent
                    portfolio_theta += pos.theta * pos.quantity * (1 if pos.instrument_type != "OPTION" else multiplier)
                if pos.vega is not None:
                    portfolio_vega += pos.vega * pos.quantity * (1 if pos.instrument_type != "OPTION" else multiplier)

        # Determine overall last_updated_at based on the freshest data component
        overall_last_updated = max(balance_last_updated, position_data_last_updated)
                                if balance_last_updated != datetime.min or position_data_last_updated != datetime.min
                                else datetime.utcnow() # Fallback if no data

        return PortfolioMetricsSchema(
            net_liquidity=net_liquidity,
            buying_power=buying_power,
            portfolio_delta=portfolio_delta if open_positions_count > 0 else None, # Null if no positions with greeks
            portfolio_gamma=portfolio_gamma if open_positions_count > 0 else None,
            portfolio_theta=portfolio_theta if open_positions_count > 0 else None,
            portfolio_vega=portfolio_vega if open_positions_count > 0 else None,
            open_positions_count=open_positions_count,
            last_updated_at=overall_last_updated
        )
```
**Important Note on Greeks:** The availability and quality of Greek values from the TastyTrade API are crucial. If they are not provided, or not reliably updated, implementing a custom Greek calculation engine is a very significant undertaking requiring an option pricing model (like Black-Scholes or Binomial) and real-time market data for all underlyings (price, volatility, interest rates). For MVP, relying on broker-provided Greeks is preferred. If unavailable, those specific metrics might be omitted or marked as N/A.
