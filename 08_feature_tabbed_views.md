# Feature 8: Tabbed Views (Calendar, Underlying, Strategy, P&L by Delta)

**Feature Goal:**
To provide users with multiple, distinct perspectives on their trading activity, P&L, and portfolio composition through a tabbed interface. Each tab will offer a specialized view (Calendar P&L, P&L by Underlying, P&L by Strategy, P&L by Delta), allowing users to drill down into specific aspects of their performance and risk. These views should be performant and scalable.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/views/{account_id}/`):**
    *   `GET /calendar`: Params: `month`, `year`.
        *   Response Schema: `CalendarViewSchema` (e.g., `List[CalendarDayPnlSchema]`, where each item has `date`, `realized_pnl`, `unrealized_pnl_change`, `total_pnl_for_day`).
    *   `GET /by-underlying`: Params: `period` (daily, mtd, ytd, custom_start, custom_end), `sort_by`.
        *   Response Schema: `List[PnlByUnderlyingViewSchema]` (e.g., `underlying_symbol`, `realized_pnl`, `unrealized_pnl`, `total_pnl`, `current_positions_summary: List[PositionSummarySchema]`).
    *   `GET /by-strategy`: Params: `period`.
        *   Response Schema: `List[PnlByStrategyViewSchema]` (e.g., `strategy_name` (auto or custom), `realized_pnl`, `unrealized_pnl`, `total_pnl`, `trade_count`).
    *   `GET /by-delta`: Params: `period`.
        *   Response Schema: `List[PnlByDeltaBucketSchema]` (e.g., `delta_range_label`, `realized_pnl`, `unrealized_pnl`, `total_pnl`, `current_market_value_in_bucket`).

**Detailed Feature Requirements:**

1.  **General Tab Navigation & Filtering:**
    *   A clear, intuitive tabbed navigation system within the main application interface (likely part of the dashboard layout).
    *   Each tab, when selected, loads its specific data view for the chosen TastyTrade account.
    *   All views must support filtering by timeframes: Current Day, Month-to-Date (MTD), Year-to-Date (YTD), and custom date ranges where applicable. API endpoints must support these period filters.
    *   Maintain state or reload data efficiently when switching tabs or changing filters.
2.  **Calendar View:**
    *   Display a calendar (e.g., monthly view).
    *   For each day with trading activity, show realized P&L and/or change in unrealized P&L for that day.
    *   Visually indicate profit (e.g., green background/text) or loss (e.g., red background/text) for each day.
    *   Allow navigation to previous/next months/years.
    *   Clicking on a day could show a summary of trades or P&L contributions for that day (optional drill-down for future enhancement).
3.  **P&L by Underlying View:**
    *   List all underlying symbols for which the user has/had positions or closed trades during the selected period.
    *   For each underlying: display aggregated realized P&L, current unrealized P&L (if positions are open), and total P&L for the selected period.
    *   Optionally, allow expanding an underlying to see individual positions/trades associated with it.
    *   Sorting options (e.g., by symbol, by total P&L).
4.  **P&L by Strategy View:**
    *   List all identified trading strategies (both auto-detected from Feature 7 and custom-defined) that have activity within the selected period.
    *   For each strategy: display aggregated realized P&L, current unrealized P&L (if positions contributing to the strategy are open), and total P&L for the selected period.
    *   Show number of trades or positions associated with each strategy.
    *   Sorting options (e.g., by strategy name, by P&L).
5.  **P&L by Delta View:**
    *   This view aims to show P&L contributions based on the Delta risk of positions.
    *   Positions (open or closed during the period) are bucketed into Delta ranges (e.g., Delta < -0.75, -0.75 <= Delta < -0.25, -0.25 <= Delta < 0.25, etc.). Delta used could be at time of trade opening, or current delta for open positions.
    *   For each Delta bucket: display aggregated P&L (realized/unrealized) from positions/trades that fell into that delta range.
    *   This is an advanced analytical view; clear definition of Delta measurement point is needed.
6.  **Data Consistency & Accuracy:**
    *   P&L figures across all views must be consistent, derived from the same core P&L calculation engine (Feature 5).
7.  **Performance & Scalability:**
    *   Data aggregation for these views can be intensive. Backend queries must be highly optimized (e.g., using appropriate database indexes, efficient joins, pre-aggregation where feasible).
    *   Consider pagination for long lists (e.g., in Underlying or Strategy views).
    *   Use loading indicators in the UI while data is being fetched for each tab.
    *   Backend may need to perform complex aggregations; ensure these don't time out for users with large datasets.
8.  **Testing:**
    *   Unit tests for backend data aggregation logic for each view.
    *   Integration tests for API endpoints serving view data with various filter combinations.
    *   Frontend component tests for displaying each view correctly.

**Detailed Implementation Guide:**

*   **Backend (FastAPI):**
    1.  **Reporting Service (`app/services/reporting_service.py`) - Enhancements:**
        *   `async def get_calendar_view_data(db: Session, user_id: int, account_id: int, month: int, year: int) -> List[CalendarDayPnlSchema]:` (Requires daily P&L snapshots or on-the-fly calculation from transactions).
        *   `async def get_pnl_by_underlying_view_data(db: Session, user_id: int, account_id: int, period_spec: PeriodSpec) -> List[PnlByUnderlyingViewSchema]:` (Aggregates P&L from Feature 5, grouped by `underlying_symbol`).
        *   `async def get_pnl_by_strategy_view_data(db: Session, user_id: int, account_id: int, period_spec: PeriodSpec) -> List[PnlByStrategyViewSchema]:` (Aggregates P&L, grouped by `strategy_name` from Feature 7).
        *   `async def get_pnl_by_delta_view_data(db: Session, user_id: int, account_id: int, period_spec: PeriodSpec) -> List[PnlByDeltaBucketSchema]:` (Requires fetching positions/trades with associated delta, then bucketing and aggregating P&L).
    2.  **Database Models & Queries:**
        *   Leverage `Transaction`, `Position`, `StrategyLink` models.
        *   May require optimized query patterns or materialized views/summary tables for performance if direct aggregation is too slow, especially for users with very large trade histories.
        *   `DailyPnlSnapshot` (from Feature 5) would be very useful for the Calendar view.
    3.  **Schemas (`app/schemas/view.py` - new or extend `report.py`):**
        *   `CalendarDayPnlSchema(BaseModel)`: `date: date`, `realized_pnl: float`, `unrealized_pnl_change: float`, `total_pnl_for_day: float`.
        *   `PositionSummarySchema(BaseModel)`: `symbol: str`, `quantity: float`, `current_market_value: float`, `unrealized_pnl: float`.
        *   `PnlByUnderlyingViewSchema(PnlDataSchema)`: `underlying_symbol: str`, `open_positions_summary: Optional[List[PositionSummarySchema]]` (extends a base PnlDataSchema with realized/unrealized/total P&L).
        *   `PnlByStrategyViewSchema(PnlDataSchema)`: `strategy_name: str`, `strategy_type: str`, `trade_count: int`.
        *   `PnlByDeltaBucketSchema(PnlDataSchema)`: `delta_bucket_label: str` (e.g., "-1.0 to -0.5"), `position_count: int`.
    4.  **API Endpoints (`app/api/v1/endpoints/views.py` - new, or extend `reports.py`):** Implement as per API Relationships, ensuring they take `account_id` as a path parameter.
*   **Frontend (Next.js):**
    1.  **Main Layout with Tabs (`src/app/(dashboard)/layout.tsx` or a dedicated layout component for these views):**
        *   Implement tab navigation UI (e.g., using `Tabs` component from `shadcn/ui`).
        *   Manage active tab state, possibly using Next.js nested routes for each tab (e.g., `/dashboard/views/calendar`, `/dashboard/views/underlying`).
    2.  **Page Components for Each Tab (`src/app/(dashboard)/views/calendar/page.tsx`, etc.):**
        *   Each page component is responsible for fetching and displaying data for its specific view.
        *   Include filter controls (date pickers, period selectors, account selector if not global).
        *   Handle loading states, error messages, and empty states.
    3.  **Reusable UI Components (`src/components/views/`):**
        *   `CalendarGrid.tsx`: Renders the calendar with P&L data.
        *   `UnderlyingPnlTable.tsx`: Table for P&L by underlying.
        *   `StrategyPnlList.tsx`: List/table for P&L by strategy.
        *   `DeltaPnlChartOrTable.tsx`: Component for P&L by Delta view.
    4.  **API Service Calls (`src/services/viewService.ts` - new, or extend `reportService.ts`):** Functions for each view, e.g., `getCalendarData(accountId, month, year)`.

**Pseudocode Example (Frontend Tab Navigation & Data Fetching - Conceptual):**

```typescript
// In a layout component src/app/(dashboard)/views/layout.tsx
// Using Next.js App Router for tab navigation

function ViewsLayout({ children, params }: { children: React.ReactNode, params: { accountId: string } }) {
  const pathname = usePathname(); // e.g., /dashboard/views/calendar

  const tabs = [
    { name: "Calendar", href: `/dashboard/views/${params.accountId}/calendar` },
    { name: "By Underlying", href: `/dashboard/views/${params.accountId}/underlying` },
    { name: "By Strategy", href: `/dashboard/views/${params.accountId}/strategy` },
    { name: "P&L by Delta", href: `/dashboard/views/${params.accountId}/pnl-by-delta` },
    { name: "Net Liquidity", href: `/dashboard/views/${params.accountId}/net-liquidity` }, // Feature 9
  ];

  return (
    <div>
      <nav> {/* Shadcn/ui Tabs component would go here */}
        {tabs.map(tab => (
          <Link key={tab.href} href={tab.href} 
                className={pathname === tab.href ? "font-bold" : ""}>
            {tab.name}
          </Link>
        ))}
      </nav>
      <main>{children}</main> {/* This will render the specific tab's page.tsx */}
    </div>
  );
}

// In a page component, e.g., src/app/(dashboard)/views/[accountId]/underlying/page.tsx
// Assume SWR or React Query for data fetching

export default function UnderlyingPnlPage({ params }: { params: { accountId: string } }) {
  const [period, setPeriod] = useState("mtd"); // Default period
  // const { data, error, isLoading } = useSWR(
  //   `/api/v1/views/${params.accountId}/by-underlying?period=${period}`,
  //   fetcherFn
  // );

  // Render period selectors, loading state, error state, and table with data
  return (
    <div>
      {/* Period selector UI, Account ID: {params.accountId} */}
      {/* {isLoading ? <p>Loading...</p> : <UnderlyingPnlTable data={data} />} */}
      <p>Underlying P&L View for account: {params.accountId}, period: {period}</p>
    </div>
  );
}
```
These tabbed views will provide users with powerful tools to analyze their trading performance from various angles, contributing significantly to the application's value.

