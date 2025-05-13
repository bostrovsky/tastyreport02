

### Feature 7: Strategy Identification & Management

**Feature Goal:**
To automatically identify common predefined trading strategies (e.g., strangles, straddles, verticals, condors) based on the user's open positions and historical trades. Additionally, to allow users to manually define, name, and tag their own custom strategies for trades or groups of trades that the system doesn't automatically recognize or for which the user has a specific classification.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/strategies/`):**
    *   `GET /identified`: (Potentially part of position/trade data, or a separate call)
        *   Request: Requires authenticated user. Query parameters for `account_id`, `position_id` (to get strategy for a specific position), or `trade_group_id`.
        *   Response Schema: `StrategySchema` (e.g., `strategy_name`, `type` (auto/custom), `description`, `involved_legs: List[PositionLegSchema]`).
    *   `POST /custom`: (For users to define/tag a custom strategy)
        *   Request Body Schema: `CustomStrategyCreateSchema` (e.g., `name`, `description`, `list_of_transaction_ids` or `list_of_position_ids` to associate).
        *   Response Schema: `StrategySchema` (the newly created/tagged custom strategy).
    *   `PUT /custom/{strategy_id}`: (To update a user-defined custom strategy).
    *   `GET /custom`: (To list all user-defined custom strategies).
*   **Internal Logic:**
    *   The `StrategyService` will contain complex logic to analyze combinations of option legs.

**Detailed Feature Requirements:**

1.  **Automatic Strategy Identification:**
    *   The system should be able to recognize common option strategies based on the legs of an open position or a group of related opening transactions. Examples:
        *   **Covered Call:** Long stock + Short call on that stock.
        *   **Cash-Secured Put:** Short put (with sufficient cash, though cash isn't directly checked by this feature, the leg combination is key).
        *   **Vertical Spreads (Debit/Credit, Call/Put):** Long option + Short option of the same type (call/put), same underlying, same expiration, different strikes.
        *   **Straddle:** Long/Short Put + Long/Short Call, same underlying, same expiration, same strike.
        *   **Strangle:** Long/Short Put + Long/Short Call, same underlying, same expiration, different out-of-the-money strikes.
        *   **Iron Condor:** Short put spread + Short call spread (four legs total).
        *   **Butterfly Spread:** Three legs, specific strike pattern.
    *   Identification should consider: instrument type (options), underlying symbol, expiration date, strike price, option type (call/put), and action (buy/sell).
    *   The system should assign a predefined name to automatically identified strategies.
2.  **Custom Strategy Definition & Tagging:**
    *   Users should be able to select one or more open positions or historical trades and assign a custom strategy name and description to them.
    *   These user-defined strategies should be saved and associated with the user's account.
    *   Provide a dropdown or autocomplete for users to select previously defined custom strategies when tagging new trades.
3.  **Strategy Storage:**
    *   Identified strategy information (whether auto-detected or custom) should be stored in the database, linked to the relevant positions or transactions.
    *   A `Strategy` model might store predefined strategy definitions and user-custom strategies.
4.  **Display of Strategies:**
    *   The identified or custom strategy name should be displayable alongside positions in various views (e.g., Underlying View, Strategy View).
5.  **Accuracy & Ambiguity:**
    *   Strategy identification can be complex and sometimes ambiguous (e.g., a set of legs could be part of multiple simpler strategies or one complex one). The system should aim for common interpretations or potentially offer the most likely one.
    *   For MVP, focus on clear, unambiguous common strategies.
6.  **Retroactive Identification (Optional for MVP):**
    *   Ability to run strategy identification on historical closed trades.

**Detailed Implementation Guide:**

*   **Backend (FastAPI):**
    1.  **Strategy Service (`services/strategy_service.py`):**
        *   `async def identify_strategy_for_positions(positions: List[PositionData]) -> Optional[IdentifiedStrategy]:`
            *   This is the core logic engine. It will take a list of position legs (e.g., for a specific underlying and expiration).
            *   Implement rule-based logic to check for patterns matching known strategies.
                *   Sort legs by strike, type (call/put).
                *   Check quantities (e.g., vertical spreads have equal quantities for long/short legs).
                *   Check strike differences, expiration dates, underlying symbols.
            *   Return the name of the identified strategy or None if no predefined strategy is matched.
            *   Example rules:
                *   *Vertical Call Spread:* 2 legs, same underlying, same expiration, both calls, one long & one short, different strikes.
                *   *Iron Condor:* 4 legs, same underlying, same expiration, one short put, one long put (lower strikes), one short call, one long call (higher strikes), specific strike relationships (e.g., short put strike < long put strike < long call strike < short call strike).
        *   `async def assign_custom_strategy(user_id: int, name: str, description: Optional[str], trade_ids: List[str]) -> CustomStrategy:`
            *   Create or retrieve a custom strategy definition.
            *   Link it to the specified trades/positions in the database.
    2.  **Database Models (`db/models/strategy.py`, enhance `Position`/`Transaction`):**
        *   `StrategyDefinition(Base)`: `id`, `name` (e.g., "Iron Condor", "User: My Special Hedge"), `type` (auto_predefined, user_custom), `description`, `rules_definition` (JSON, optional, for complex auto-rules).
        *   `Position` model: Add `identified_strategy_id: Optional[ForeignKey(StrategyDefinition.id)]`, `custom_strategy_id: Optional[ForeignKey(StrategyDefinition.id)]`.
        *   `TransactionGroup` or `Trade` model (if trades are explicitly grouped beyond individual transactions): Could also link to a strategy.
    3.  **CRUD Operations (`crud/crud_strategy.py`):**
        *   For managing `StrategyDefinition` (creating custom ones, fetching predefined).
        *   For linking strategies to positions/trades.
    4.  **API Endpoints (`api/v1/endpoints/strategies.py`):**
        *   Implement endpoints as per API Relationships for creating/managing custom strategies and potentially for triggering identification on demand (though identification might primarily happen during data sync/processing).
    5.  **Integration with Data Sync (Feature 2):**
        *   After new positions are synced, the `StrategyService.identify_strategy_for_positions` could be called to attempt to automatically tag them.
*   **Frontend (Next.js):**
    1.  **Displaying Strategies:**
        *   In position tables or trade detail views, display the `strategy_name` if available.
    2.  **Custom Strategy Management UI (Optional for MVP, could be a later enhancement):**
        *   A section where users can view their custom strategies.
        *   A modal or form to select trades/positions and assign/create a custom strategy tag.
        *   Dropdown for selecting existing custom strategy names.

**Pseudocode Example (Strategy Identification Snippet - very simplified):**

```python
# In services/strategy_service.py

def is_vertical_call_spread(legs: List[PositionLegSchema]) -> bool:
    if len(legs) != 2: return False
    leg1, leg2 = sorted(legs, key=lambda x: x.strike_price) # Sort by strike

    # Check common underlying, expiration, both calls
    if not (leg1.underlying == leg2.underlying and
            leg1.expiration == leg2.expiration and
            leg1.option_type == "CALL" and leg2.option_type == "CALL"):
        return False

    # Check one long, one short, same quantity (absolute)
    if not ((leg1.action_type == "LONG" and leg2.action_type == "SHORT") or
            (leg1.action_type == "SHORT" and leg2.action_type == "LONG")):
        return False
    if abs(leg1.quantity) != abs(leg2.quantity):
        return False

    # Leg1 has lower strike, Leg2 has higher strike
    # Long Call Spread: Long lower_strike_call, Short higher_strike_call (Debit)
    # Short Call Spread: Short lower_strike_call, Long higher_strike_call (Credit)
    # This function just identifies it as a "Vertical Call Spread" generically
    return True

async def identify_strategy_for_position_group(self, position_legs: List[PositionLegSchema]) -> Optional[str]:
    # Ensure all legs share same underlying and expiration for many common strategies
    if not position_legs: return None
    main_underlying = position_legs[0].underlying
    main_expiration = position_legs[0].expiration
    if not all(p.underlying == main_underlying and p.expiration == main_expiration for p in position_legs):
        # Legs are for different underlyings/expirations, handle as individual legs or simpler groups
        if len(position_legs) == 1 and position_legs[0].option_type: # Single option leg
             return f"Single {position_legs[0].action_type} {position_legs[0].option_type}"
        return "Custom / Mixed Legs"

    if is_vertical_call_spread(position_legs):
        return "Vertical Call Spread"
    # elif is_iron_condor(position_legs): # More complex check for 4 legs
    #     return "Iron Condor"
    # ... other strategy checks (straddle, strangle, put spreads, etc.)

    if len(position_legs) == 1 and position_legs[0].option_type: # Re-check for single after group checks
        return f"Single {position_legs[0].action_type} {position_legs[0].option_type}"
    elif len(position_legs) == 1 and not position_legs[0].option_type: # Stock position
        return f"{position_legs[0].action_type} Stock"

    return "Unidentified Spread / Custom"
```
**Note:** Building a comprehensive and accurate automatic strategy identification engine is a significant undertaking. For MVP, it might be limited to a few very common and easily identifiable strategies. The custom tagging feature is crucial to allow users to manage their own classifications regardless of the auto-detection capabilities.




### Feature 8: Tabbed Views (Calendar, Underlying, Strategy, P&L by Delta)

**Feature Goal:**
To provide users with multiple, distinct perspectives on their trading activity, P&L, and portfolio composition through a tabbed interface. Each tab will offer a specialized view (Calendar, Underlying, Strategy, P&L by Delta), allowing users to drill down into specific aspects of their performance and risk.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/views/` or extend `/api/v1/reports/`):**
    *   `GET /calendar`:
        *   Request: Auth user. Params: `account_id` (optional), `month`, `year`.
        *   Response Schema: `CalendarViewSchema` (e.g., `List[CalendarDayPnlSchema]`, where each item has `date`, `realized_pl`, `unrealized_pl_change`, `total_pl_for_day`).
    *   `GET /underlying`:
        *   Request: Auth user. Params: `account_id` (optional), `period` (daily, mtd, ytd, custom_start, custom_end), `sort_by` (e.g., symbol, total_pnl).
        *   Response Schema: `List[PnlByUnderlyingViewSchema]` (e.g., `underlying_symbol`, `realized_pl`, `unrealized_pl`, `total_pl`, `current_positions_summary: List[PositionSummarySchema]`).
    *   `GET /strategy`:
        *   Request: Auth user. Params: `account_id` (optional), `period`.
        *   Response Schema: `List[PnlByStrategyViewSchema]` (e.g., `strategy_name` (auto or custom), `realized_pl`, `unrealized_pl`, `total_pl`, `trade_count`).
    *   `GET /pnl-by-delta`:
        *   Request: Auth user. Params: `account_id` (optional), `period`.
        *   Response Schema: `List[PnlByDeltaBucketSchema]` (e.g., `delta_range_or_bucket_name`, `realized_pl`, `unrealized_pl`, `total_pl`, `current_market_value_in_bucket`). This is more complex and might require bucketing positions by their delta values.

**Detailed Feature Requirements:**

1.  **General Tab Navigation:**
    *   A clear, intuitive tabbed navigation system within the main application interface.
    *   Each tab, when selected, loads its specific data view.
    *   Maintain state or reload data appropriately when switching tabs.
    *   All views should support filtering by timeframes: Current Day, Month-to-Date (MTD), and Year-to-Date (YTD), as specified in original requirements. The API endpoints should support these period filters.
2.  **Calendar View:**
    *   Display a calendar (e.g., monthly view).
    *   For each day with trading activity, show realized P&L and/or change in unrealized P&L for that day.
    *   Visually indicate profit (green) or loss (red) for each day.
    *   Allow navigation to previous/next months/years.
    *   Clicking on a day might show a summary of trades or P&L contributions for that day (optional drill-down).
3.  **Underlying View:**
    *   List all underlying symbols for which the user has/had positions during the selected period.
    *   For each underlying: display aggregated realized P&L, current unrealized P&L (if positions are open), and total P&L for the selected period.
    *   Optionally, allow expanding an underlying to see individual positions/trades associated with it.
    *   Sorting options (e.g., by symbol, by P&L).
4.  **Strategy View:**
    *   List all identified trading strategies (both auto-detected from Feature 7 and custom-defined) that have activity within the selected period.
    *   For each strategy: display aggregated realized P&L, current unrealized P&L (if positions contributing to the strategy are open), and total P&L for the selected period.
    *   Show number of trades or positions associated with each strategy.
    *   Sorting options (e.g., by strategy name, by P&L).
5.  **P&L by Delta View:**
    *   This view aims to show P&L contributions based on the risk level (Delta) of positions.
    *   Positions could be bucketed into Delta ranges (e.g., highly negative delta, near-neutral delta, highly positive delta).
    *   For each Delta bucket: display aggregated P&L (realized/unrealized) from positions that fell into that delta range during the period or at a point in time.
    *   This is a more advanced analytical view and might require careful definition of how delta is measured (e.g., delta at the time of trade, current delta of open positions).
6.  **Data Consistency:**
    *   P&L figures across all views should be consistent, derived from the same core P&L calculation engine (Feature 5).
7.  **Performance:**
    *   Data aggregation for these views can be intensive. Backend queries must be optimized.
    *   Consider pagination for long lists (e.g., in Underlying or Strategy views).
    *   Use loading indicators while data is being fetched for each tab.

**Detailed Implementation Guide:**

*   **Backend (FastAPI):**
    1.  **Reporting Service (`services/reporting_service.py`) - Enhancements:**
        *   `async def get_calendar_view_data(db: Session, user_id: int, month: int, year: int) -> List[CalendarDayPnlSchema]:`
            *   Fetch daily P&L data (realized, and change in unrealized if tracked daily) for the given month/year.
            *   Requires daily snapshots or calculations of P&L.
        *   `async def get_underlying_view_data(db: Session, user_id: int, period_spec: PeriodSpec) -> List[PnlByUnderlyingViewSchema]:`
            *   Fetch trades/positions for the period.
            *   Aggregate P&L (realized and unrealized) grouped by `underlying_symbol`.
        *   `async def get_strategy_view_data(db: Session, user_id: int, period_spec: PeriodSpec) -> List[PnlByStrategyViewSchema]:`
            *
(Content truncated due to size limit. Use line ranges to read in chunks)
