# Feature 4: Dashboard

**Feature Goal:**
To provide users with a centralized, at-a-glance overview of their key portfolio metrics, P&L summary, market conditions, and potentially actionable insights or alerts. The dashboard should be the primary landing page after login and offer a clear, concise, and customizable summary of their trading world, designed for scalability and reliability.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/dashboard/`):**
    *   `GET /summary/{account_id}`: (To fetch all necessary data for the dashboard for a specific linked TastyTrade account).
        *   Request: Requires authenticated user, `account_id` (or an identifier for the user's primary/selected TastyTrade account) as a path parameter.
        *   Response Schema: `DashboardSummarySchema` (a composite schema including P&L summary, key portfolio metrics, market overview data (could be a sub-schema or fetched separately by frontend), and potentially recent activity/alerts).
    *   (Alternatively, the frontend might make multiple calls to different existing endpoints, e.g., `/market-data/overview`, `/reports/pnl-summary/{account_id}`, `/reports/portfolio-metrics/{account_id}`. A dedicated dashboard endpoint is often better for performance by reducing chattiness).

**Detailed Feature Requirements:**

1.  **Key Information Display:** The dashboard must prominently display:
    *   **Market Overview:** (Leveraging Feature 3) Display S&P 500, NASDAQ, Dow Jones, VIX with current values and changes.
    *   **Account P&L Summary:**
        *   Daily P&L (Realized + Unrealized change for the current trading day).
        *   Month-to-Date (MTD) P&L (Realized + Unrealized change).
        *   Year-to-Date (YTD) P&L (Realized + Unrealized change).
        *   Overall P&L (Total Realized P&L + Current Unrealized P&L for all time or since account linking).
    *   **Key Portfolio Metrics:** (Leveraging Feature 6)
        *   Net Liquidity (current).
        *   Buying Power (current).
        *   Portfolio Delta (overall, and potentially broken down by underlying if space allows or via a small chart).
        *   Portfolio Theta (overall).
        *   Portfolio Vega (overall).
        *   Number of Open Positions.
    *   **Account Selection:** If the user has multiple TastyTrade accounts linked, provide a clear way to select which account's data is displayed on the dashboard.
2.  **Layout & Customization (Future Enhancement for Customization):**
    *   **MVP Layout:** A clean, well-organized layout that presents information logically. Information should be grouped into clear sections or cards.
    *   **Future:** Allow users to customize the dashboard by adding, removing, or rearranging widgets/cards.
3.  **Visualizations (Optional for MVP, but Recommended):**
    *   Small P&L trend chart (e.g., daily P&L for the last 7 days).
    *   Portfolio allocation chart (e.g., by underlying, by strategy - could be simplified for MVP).
4.  **Recent Activity/Alerts (Optional for MVP):**
    *   A small section for recent significant trades, large P&L swings, or important notifications (e.g., upcoming expirations, margin calls if this data is available and processed).
5.  **Responsiveness & Performance:**
    *   The dashboard should load quickly and be responsive across different screen sizes (desktop primarily for MVP, mobile responsiveness as a plus).
    *   Data fetching should be optimized. A single aggregated API call for dashboard data is preferable to many small calls from the frontend.
6.  **Data Freshness:**
    *   Clearly indicate the last updated time for P&L and portfolio metrics.
    *   Market data will have its own update timestamp.
7.  **Testing:**
    *   Unit tests for any backend aggregation logic for the dashboard.
    *   Frontend component tests for dashboard widgets.
    *   Integration tests for fetching and displaying dashboard data.

**Detailed Implementation Guide:**

*   **Backend (FastAPI):**
    1.  **Dashboard Service (`app/services/dashboard_service.py` - new or extend `reporting_service.py`):**
        *   `async def get_dashboard_summary(db: Session, user_id: int, tastytrade_account_id: int) -> DashboardSummarySchema:`
            *   This service method will orchestrate fetching data from other services or CRUD layers:
                *   Call `PnlService` (Feature 5) to get Daily, MTD, YTD P&L summaries.
                *   Call `PortfolioMetricsService` (Feature 6) to get current Net Liq, BP, Delta, Theta, Vega, etc.
                *   (Market data might be fetched by frontend directly from `MarketDataService` or included here if a single backend call is preferred).
            *   Aggregate this data into the `DashboardSummarySchema`.
    2.  **Schemas (`app/schemas/dashboard.py` - new):**
        *   `PnlSummaryWidgetSchema(BaseModel)`: `daily_pnl: float`, `mtd_pnl: float`, `ytd_pnl: float`, `overall_pnl: float`, `last_updated: datetime`.
        *   `PortfolioMetricsWidgetSchema(BaseModel)`: `net_liquidity: float`, `buying_power: float`, `portfolio_delta: float`, `portfolio_theta: float`, `portfolio_vega: float`, `open_positions_count: int`, `last_updated: datetime`.
        *   `DashboardSummarySchema(BaseModel)`: `account_name: str`, `pnl_summary: PnlSummaryWidgetSchema`, `portfolio_metrics: PortfolioMetricsWidgetSchema`, `market_overview: Optional[MarketOverviewSchema]` (from Feature 3 schema), `alerts: Optional[List[AlertSchema]]`.
    3.  **API Endpoint (`app/api/v1/endpoints/dashboard.py` - new):**
        *   Implement `GET /summary/{account_id}` endpoint, calling `dashboard_service.get_dashboard_summary()`.
        *   Ensure proper authentication and authorization (user can only access their own account data).
*   **Frontend (Next.js):**
    1.  **Dashboard Page (`src/app/(dashboard)/page.tsx`):**
        *   This will be the main component for the dashboard.
        *   On load, fetch data from the backend `/api/v1/dashboard/summary/{account_id}` endpoint.
        *   Use state management (React Context, Zustand, or Redux) to hold dashboard data.
        *   Display loading states while data is being fetched.
        *   Handle and display error messages if data fetching fails.
        *   Allow account selection if multiple accounts are linked, and refetch data when account changes.
    2.  **Dashboard Widgets/Components (`src/components/dashboard/`):**
        *   `MarketOverviewWidget.tsx`: (Reuses or adapts component from Feature 3) Displays market indices.
        *   `PnlSummaryWidget.tsx`: Displays daily, MTD, YTD, overall P&L.
        *   `PortfolioMetricsWidget.tsx`: Displays Net Liq, BP, Delta, Theta, etc.
        *   `AccountSelectorDropdown.tsx`: If multiple accounts.
        *   (Optional MVP) `PnlTrendChart.tsx`, `RecentActivityWidget.tsx`.
        *   These components will receive data as props from the main `DashboardPage`.
    3.  **API Service Call (`src/services/dashboardService.ts` - new):**
        *   `async function getDashboardSummary(accountId: string): Promise<DashboardSummarySchema>`.
    4.  **Styling:**
        *   Use Tailwind CSS (or chosen styling solution) to create a visually appealing and organized layout.
        *   Ensure cards or sections are clearly delineated.

**Pseudocode Example (Backend Dashboard Service):**

```python
# In app/services/dashboard_service.py

from app.services.pnl_service import PnlService # Assumes Feature 5 service
from app.services.portfolio_metrics_service import PortfolioMetricsService # Assumes Feature 6 service
from app.services.market_data_service import MarketDataService # Assumes Feature 3 service
from app.schemas.dashboard import DashboardSummarySchema, PnlSummaryWidgetSchema, PortfolioMetricsWidgetSchema
from app.crud import crud_tastytrade_account

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.pnl_service = PnlService(db)
        self.metrics_service = PortfolioMetricsService(db)
        self.market_service = MarketDataService() # May not need db if cache-based

    async def get_dashboard_summary(self, user_id: int, tastytrade_db_account_id: int) -> DashboardSummarySchema:
        db_account = await crud_tastytrade_account.get(self.db, id=tastytrade_db_account_id)
        if not db_account or db_account.user_id != user_id:
            raise HTTPException(status_code=404, detail="Account not found or not authorized")

        account_number = db_account.account_number

        # Fetch P&L Data
        daily_pnl = await self.pnl_service.get_daily_pnl(account_number)
        mtd_pnl = await self.pnl_service.get_mtd_pnl(account_number)
        ytd_pnl = await self.pnl_service.get_ytd_pnl(account_number)
        overall_pnl = await self.pnl_service.get_overall_pnl(account_number)
        pnl_summary = PnlSummaryWidgetSchema(
            daily_pnl=daily_pnl.total_pnl,
            mtd_pnl=mtd_pnl.total_pnl,
            ytd_pnl=ytd_pnl.total_pnl,
            overall_pnl=overall_pnl.total_pnl,
            last_updated=datetime.utcnow() # Or more specific P&L calculation time
        )

        # Fetch Portfolio Metrics
        metrics = await self.metrics_service.get_current_portfolio_metrics(account_number)
        portfolio_metrics = PortfolioMetricsWidgetSchema(
            net_liquidity=metrics.net_liquidity,
            buying_power=metrics.buying_power,
            portfolio_delta=metrics.portfolio_delta,
            portfolio_theta=metrics.portfolio_theta,
            portfolio_vega=metrics.portfolio_vega,
            open_positions_count=metrics.open_positions_count,
            last_updated=metrics.last_updated_at
        )

        # Fetch Market Overview (can also be fetched client-side)
        market_overview = await self.market_service.get_market_overview_data()

        return DashboardSummarySchema(
            account_name=db_account.account_nickname or account_number, # Assuming a nickname field
            pnl_summary=pnl_summary,
            portfolio_metrics=portfolio_metrics,
            market_overview=market_overview,
            alerts=[] # Placeholder for MVP
        )

```
The dashboard serves as the central hub for the user, so its clarity, accuracy, and performance are paramount to a good user experience.
