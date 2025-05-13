# Feature 5: P&L Calculation & Reporting

**Feature Goal:**
To accurately calculate and report Profit & Loss (P&L) for the user's trading activities. This includes Realized P&L from closed trades/transactions and Unrealized P&L for open positions. Calculations should be available for various timeframes (Daily, MTD, YTD, custom) and aggregations (overall, by underlying, by strategy), ensuring accuracy, reliability, and scalability.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/reports/`):**
    *   `GET /pnl/summary/{account_id}`:
        *   Request: Auth user, `account_id`. Query params: `period` (e.g., "daily", "mtd", "ytd", "all_time", or `start_date`, `end_date`).
        *   Response Schema: `PnlSummaryReportSchema` (e.g., `period_start`, `period_end`, `realized_pnl`, `unrealized_pnl_change`, `total_pnl`, `fees_commissions_total`).
    *   `GET /pnl/by-underlying/{account_id}`:
        *   Request: Auth user, `account_id`. Query params: `period`.
        *   Response Schema: `List[PnlByUnderlyingSchema]` (each item: `underlying_symbol`, `realized_pnl`, `unrealized_pnl`, `total_pnl`).
    *   `GET /pnl/by-trade/{account_id}`: (For detailed trade-level P&L)
        *   Request: Auth user, `account_id`. Query params: `period`, `trade_id` (optional, for a specific trade).
        *   Response Schema: `List[TradePnlSchema]` (each item: `trade_open_date`, `trade_close_date`, `symbol`, `quantity`, `open_price`, `close_price`, `realized_pnl`).

**Detailed Feature Requirements:**

1.  **Realized P&L Calculation:**
    *   Calculate realized P&L for all closed trades (options, stocks, futures if applicable).
    *   Methodology: Typically FIFO (First-In, First-Out) for stocks, or specific lot matching if data is available. For options, it's often simpler: (Proceeds from closing/expiration - Cost of opening) * Quantity * Multiplier - Commissions/Fees.
    *   Must accurately account for commissions and fees associated with each trade.
    *   Handle assignments and expirations correctly (e.g., option assignment results in a stock position, expiration P&L is premium received/paid if OTM, or intrinsic value if ITM minus premium).
    *   Data source: `Transaction` records synced from TastyTrade.
2.  **Unrealized P&L Calculation:**
    *   Calculate unrealized P&L for all currently open positions.
    *   Methodology: (Current Market Price - Average Open Price) * Quantity * Multiplier.
    *   Requires current market prices for all open positions (can be fetched via Feature 3 or more specific position pricing from TastyTrade API if available during sync).
    *   Average Open Price needs to be accurately tracked, considering multiple opening trades for the same position.
3.  **Total P&L:**
    *   Sum of Realized P&L (for a period) and change in Unrealized P&L (for a period for open positions), or current Unrealized P&L for an overall snapshot.
4.  **Timeframes for Reporting:**
    *   **Daily P&L:** P&L for the current trading day (or a selected past day).
    *   **Month-to-Date (MTD) P&L.**
    *   **Year-to-Date (YTD) P&L.**
    *   **Custom Date Range P&L.**
    *   **All-Time P&L:** Since account linking or start of available data.
5.  **Aggregation Levels:**
    *   Overall account P&L.
    *   P&L by underlying symbol.
    *   P&L by individual trade/strategy (Feature 7).
6.  **Accuracy & Reconciliation:**
    *   Calculations should be as accurate as possible, aiming to match broker-reported figures where feasible, though methodologies can differ.
    *   Clearly state assumptions if any are made (e.g., FIFO for stocks if not explicitly provided by broker for tax lots).
7.  **Data Storage for P&L:**
    *   While P&L can be calculated on-the-fly for reporting, consider storing daily P&L snapshots or aggregated P&L figures for performance, especially for historical reporting and charting.
    *   Store calculated realized P&L per closed trade/lot.
8.  **Handling Corporate Actions (Future Enhancement):**
    *   For MVP, focus on direct trading P&L. Future: stock splits, dividends (if not treated as simple cash), mergers can affect cost basis and P&L.
9.  **Performance:**
    *   P&L calculations, especially for long historical periods or many trades, can be intensive. Optimize database queries and calculation logic.
    *   Consider pre-calculating and storing some P&L figures via background tasks if on-the-fly calculation is too slow for common views.
10. **Testing:**
    *   Extensive unit tests with various trade scenarios (simple trades, multi-leg options, assignments, expirations, different fee structures) to verify P&L calculation accuracy.
    *   Integration tests for API endpoints serving P&L data.

**Detailed Implementation Guide:**

*   **Backend (FastAPI):**
    1.  **P&L Service (`app/services/pnl_service.py`):**
        *   `async def calculate_realized_pnl_for_trade(db: Session, trade_transactions: List[Transaction]) -> RealizedTradePnlResult:`
            *   Logic to identify opening/closing legs of a trade, sum costs/proceeds, factor in fees.
        *   `async def get_realized_pnl_for_period(db: Session, account_id: int, start_date: datetime, end_date: datetime) -> PnlPeriodResult:`
            *   Fetches relevant transactions, identifies closed trades within the period, sums their P&L.
        *   `async def get_unrealized_pnl_for_open_positions(db: Session, account_id: int) -> Dict[str, UnrealizedPositionPnlResult]:`
            *   Fetches open positions and their current market prices (may need to call `MarketDataService` or use prices from sync).
            *   Calculates unrealized P&L for each.
        *   `async def get_pnl_summary_for_period(db: Session, account_id: int, period_spec: PeriodSpec) -> PnlSummaryReportSchema:`
            *   Combines realized P&L for the period and the change in unrealized P&L over that period.
        *   Methods for P&L by underlying, by strategy, etc.
    2.  **Database Models (`app/db/models/`):**
        *   `Transaction` model is key, needs fields for `price_per_unit`, `quantity`, `commission`, `fees`, `action_type` (buy/sell, open/close), `symbol`, `underlying_symbol`, `instrument_type`, `multiplier` (for options/futures).
        *   `Position` model for `average_open_price`, `cost_basis`.
        *   (Optional) `ClosedTradeLog`: Stores details of each closed trade and its calculated realized P&L.
        *   (Optional) `DailyPnlSnapshot`: Stores `date`, `account_id`, `realized_pnl_day`, `unrealized_pnl_change_day`, `total_pnl_day`.
    3.  **CRUD Operations (`app/crud/`):**
        *   `crud_transaction.py`: Efficiently fetch transactions by period, symbol, etc.
        *   `crud_position.py`: Fetch open positions.
    4.  **Schemas (`app/schemas/report.py`, `app/schemas/pnl.py` - new or extend):**
        *   `PnlSummaryReportSchema`, `PnlByUnderlyingSchema`, `TradePnlSchema`.
        *   Internal schemas for calculation results: `RealizedTradePnlResult`, `UnrealizedPositionPnlResult`, `PnlPeriodResult`.
    5.  **API Endpoints (`app/api/v1/endpoints/reports.py`):**
        *   Implement endpoints as per API Relationships, calling methods in `PnlService`.
    6.  **Background Tasks (Optional, `app/background_tasks/pnl_tasks.py`):**
        *   Task to pre-calculate and store daily P&L snapshots.
        *   Task to calculate and store realized P&L for newly closed trades.
*   **Frontend (Next.js):**
    1.  **P&L Display Components (`src/components/reports/`, `src/components/dashboard/`):**
        *   Components to display P&L summaries (e.g., in Dashboard widgets).
        *   Tables or lists to display P&L by underlying, by trade (e.g., in dedicated report views or tabs from Feature 8).
        *   Use client-side formatting for currency values.
    2.  **API Service Calls (`src/services/reportService.ts`):**
        *   Functions to fetch P&L data from backend API endpoints.

**Pseudocode Example (Simplified Realized P&L for a Single Option Trade):**

```python
# In app/services/pnl_service.py (conceptual)

async def calculate_option_trade_pnl(opening_transaction: Transaction, closing_transaction: Transaction) -> float:
    # Assuming simple open and close of the same option contract
    # opening_transaction.action_type could be "BUY_TO_OPEN" or "SELL_TO_OPEN"
    # closing_transaction.action_type could be "SELL_TO_CLOSE" or "BUY_TO_CLOSE"

    # Cost for opening leg
    open_cost_per_contract = opening_transaction.price_per_unit
    open_total_cost = (open_cost_per_contract * opening_transaction.quantity * opening_transaction.multiplier) + 
                        opening_transaction.commission + opening_transaction.fees
    if opening_transaction.action_type.startswith("SELL"): # Credit spread, sold to open
        open_total_cost = -open_total_cost # Represents cash inflow

    # Proceeds from closing leg
    close_proceeds_per_contract = closing_transaction.price_per_unit
    close_total_proceeds = (close_proceeds_per_contract * closing_transaction.quantity * closing_transaction.multiplier) - 
                             closing_transaction.commission - closing_transaction.fees
    if closing_transaction.action_type.startswith("BUY"): # Debit spread, bought to close
        close_total_proceeds = -close_total_proceeds # Represents cash outflow
    
    # P&L Calculation
    # If sold to open (credit), P&L = Initial Credit - Cost to Close (if any)
    # If bought to open (debit), P&L = Proceeds from Close - Initial Debit
    # This can be simplified: Net proceeds from closing - Net cost of opening
    # For a SELL_TO_OPEN then BUY_TO_CLOSE: P&L = (Initial Premium Received - CommissionOpen) - (CostToBuyBack + CommissionClose)
    # For a BUY_TO_OPEN then SELL_TO_CLOSE: P&L = (PremiumFromSale - CommissionClose) - (InitialCost + CommissionOpen)

    # Simplified: if we treat costs as positive and proceeds as positive
    # and then adjust based on overall direction. Or, always: Sum of all cash flows related to the trade.
    # Let's use a cash flow approach: positive for inflow, negative for outflow.
    
    cash_flow_open = 0
    if opening_transaction.action_type.startswith("SELL"): # Sell to Open (credit)
        cash_flow_open = (opening_transaction.price_per_unit * opening_transaction.quantity * opening_transaction.multiplier) - 
                           opening_transaction.commission - opening_transaction.fees
    elif opening_transaction.action_type.startswith("BUY"): # Buy to Open (debit)
        cash_flow_open = -((opening_transaction.price_per_unit * opening_transaction.quantity * opening_transaction.multiplier) + 
                            opening_transaction.commission + opening_transaction.fees)

    cash_flow_close = 0
    if closing_transaction.action_type.startswith("SELL"): # Sell to Close (credit)
        cash_flow_close = (closing_transaction.price_per_unit * closing_transaction.quantity * closing_transaction.multiplier) - 
                            closing_transaction.commission - closing_transaction.fees
    elif closing_transaction.action_type.startswith("BUY"): # Buy to Close (debit)
        cash_flow_close = -((closing_transaction.price_per_unit * closing_transaction.quantity * closing_transaction.multiplier) + 
                             closing_transaction.commission + closing_transaction.fees)
    
    realized_pnl = cash_flow_open + cash_flow_close
    return realized_pnl
```
**Important Considerations for P&L:**
*   **Tax Lot Accounting:** For stocks, true P&L for tax purposes requires specific lot identification (FIFO, LIFO, specific ID). TastyTrade API might provide this for closed lots. If not, FIFO is a common default but should be stated.
*   **Wash Sales:** Complex tax rule, likely out of scope for MVP P&L reporting but good to be aware of for advanced versions.
*   **Currency:** Assume all calculations are in USD unless multi-currency support is a requirement.

Accurate P&L reporting is a cornerstone of a trading analytics application. Rigorous testing and clear methodology are essential.

