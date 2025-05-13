# Feature 9: Net Liquidity Tab

**Feature Goal:**
To provide users with a clear and transparent reconciliation of their account's net liquidity over specified periods (Day, MTD, YTD, custom). This view will detail the components contributing to changes in net liquidity, including starting net liquidity, realized P&L, fees, commissions, cash movements (deposits/withdrawals), other adjustments, and ending net liquidity. This feature is crucial for users to understand their account's cash flow and overall value changes.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/views/{account_id}/` or `/api/v1/reports/{account_id}/`):**
    *   `GET /net-liquidity-reconciliation`:
        *   Request: Requires authenticated user. Path param `account_id`. Query parameters for `period` (e.g., "daily", "mtd", "ytd", or custom `start_date`, `end_date`).
        *   Response Schema: `NetLiquidityReconciliationSchema` (e.g., `period_start`, `period_end`, `starting_net_liquidity`, `realized_pnl`, `fees_and_commissions`, `cash_deposits`, `cash_withdrawals`, `other_adjustments`, `calculated_ending_nl_before_unrealized`, `unrealized_pnl_change_for_period`, `ending_net_liquidity_reported`).

**Detailed Feature Requirements:**

1.  **Reconciliation Components:** The view must clearly display the following components for the selected period:
    *   **Starting Net Liquidity:** Net liquidity at the beginning of the selected period (from broker data).
    *   **Realized P&L:** Total realized profit or loss during the period (from Feature 5).
    *   **Fees & Commissions:** Total fees and commissions paid during the period (summed from transaction data, distinct from P&L calculation if P&L is net of fees).
    *   **Cash Deposits:** Total cash deposited into the account during the period.
    *   **Cash Withdrawals:** Total cash withdrawn from the account during the period.
    *   **Other Adjustments (Optional but good to consider):** Any other transactions affecting cash or value not covered above (e.g., interest paid/received, stock dividends received if treated as cash, effects of assignments/exercises if they have direct cash implications not captured in realized P&L of the option itself).
    *   **Calculated Ending Net Liquidity (Before Unrealized Changes):** Starting NL + Realized P&L - Fees & Commissions + Deposits - Withdrawals + Other Adjustments.
    *   **Change in Unrealized P&L for the Period:** The difference between the broker-reported Ending Net Liquidity and the Calculated Ending Net Liquidity (Before Unrealized Changes). This highlights the impact of market movements on open positions.
    *   **Ending Net Liquidity (Broker Reported):** Net liquidity at the end of the selected period (from broker data).
2.  **Timeframes & Filtering:**
    *   Must support standard timeframes: Current Day, Month-to-Date (MTD), Year-to-Date (YTD).
    *   Allow for custom date range selection for the reconciliation.
    *   Support selection of the specific linked TastyTrade account.
3.  **Data Source & Accuracy:**
    *   **Starting/Ending Net Liquidity (Broker Reported):** These figures should be based on TastyTrade's reported net liquidity at the start/end of the period. This requires fetching historical account balance snapshots (from Feature 2 sync, if available from TastyTrade API) or calculating based on the earliest available NL and rolling forward.
    *   **Realized P&L, Fees, Commissions:** Derived from the application's transaction data (synced from TastyTrade).
    *   **Cash Deposits/Withdrawals:** Identified from specific transaction types from TastyTrade (e.g., `MONEY_MOVEMENT` type).
    *   The reconciliation aims to explain the *change* in net liquidity. The 
