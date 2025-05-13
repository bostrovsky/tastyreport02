# Feature 7: Strategy Identification & Management

**Feature Goal:**
To automatically identify common predefined trading strategies (e.g., strangles, straddles, verticals, condors) based on the user's open positions and historical trades. Additionally, to allow users to manually define, name, and tag their own custom strategies for trades or groups of trades that the system doesn't automatically recognize or for which the user has a specific classification. This feature should be scalable to handle numerous user positions and strategies.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/strategies/`):**
    *   `GET /identified/{account_id}`:
        *   Request: Auth user, `account_id`. Query params: `position_id` (optional, to get strategy for a specific position group), `underlying_symbol` (optional).
        *   Response Schema: `List[IdentifiedStrategySchema]` (e.g., `strategy_name`, `type` (auto_predefined/user_custom), `description`, `involved_legs: List[PositionLegSchema]`, `associated_trade_ids: List[str]`).
    *   `POST /custom/{account_id}`: (For users to define/tag a custom strategy)
        *   Request Body Schema: `CustomStrategyCreateSchema` (e.g., `name`, `description`, `list_of_transaction_ids` or `list_of_position_ids` to associate).
        *   Response Schema: `CustomStrategyReadSchema`.
    *   `PUT /custom/{account_id}/{strategy_id}`: (To update a user-defined custom strategy).
        *   Request Body Schema: `CustomStrategyUpdateSchema`.
        *   Response Schema: `CustomStrategyReadSchema`.
    *   `DELETE /custom/{account_id}/{strategy_id}`: (To delete a user-defined custom strategy).
    *   `GET /custom/{account_id}`: (To list all user-defined custom strategies for an account).
        *   Response Schema: `List[CustomStrategyReadSchema]`.

**Detailed Feature Requirements:**

1.  **Automatic Strategy Identification (Rule-Based):**
    *   The system should recognize common option strategies based on the legs of an open position or a group of related opening transactions for a specific underlying and expiration. Examples:
        *   **Covered Call:** Long stock + Short call on that stock.
        *   **Cash-Secured Put:** Short put.
        *   **Vertical Spreads (Debit/Credit, Call/Put):** Long option + Short option of the same type, same underlying, same expiration, different strikes.
        *   **Straddle/Strangle:** Combinations of calls and puts with same/different strikes.
        *   **Iron Condor/Butterfly:** More complex multi-leg strategies.
    *   Identification logic should consider: instrument type, underlying symbol, expiration date, strike price, option type (call/put), quantity, and action (buy/sell, open/close).
    *   Assign a predefined name (e.g., "Iron Condor", "Short Put Vertical") to automatically identified strategies.
    *   The identification process should ideally run as part of the data sync (Feature 2) when new positions or trades are processed.
2.  **Custom Strategy Definition & Tagging:**
    *   Users should be able to select one or more open positions or historical trades and assign a custom strategy name and description to them.
    *   These user-defined strategies should be saved and associated with the user's account and the specific TastyTrade account number.
    *   Allow users to edit or delete their custom strategy definitions.
3.  **Strategy Storage & Association:**
    *   Identified strategy information (whether auto-detected or custom) should be stored in the database.
    *   A `StrategyDefinition` table could store predefined strategy rules and user-custom strategy names/descriptions.
    *   A linking table (e.g., `PositionStrategyLink` or `TradeStrategyLink`) should associate positions/trades with a `StrategyDefinition`.
4.  **Display of Strategies:**
    *   The identified or custom strategy name should be displayable alongside positions in various views (e.g., Underlying View, Strategy View - Feature 8).
    *   Allow filtering and grouping by strategy in reports and views.
5.  **Accuracy & Ambiguity Handling:**
    *   Strategy identification can be complex. The system should aim for common interpretations. For MVP, focus on a core set of unambiguous strategies.
    *   If multiple strategies could apply, the system might pick the most encompassing or allow user clarification (future enhancement).
6.  **Retroactive Identification:**
    *   Ability to run strategy identification on historical closed trades to categorize past performance.
7.  **Performance:**
    *   Strategy identification logic, especially if run on many positions, needs to be performant. If complex, consider optimizing or running it in background tasks.
8.  **Testing:**
    *   Unit tests for the rule-based strategy identification logic with various leg combinations.
    *   Integration tests for creating, updating, deleting, and associating custom strategies.

**Detailed Implementation Guide:**

*   **Backend (FastAPI):**
    1.  **Strategy Service (`app/services/strategy_service.py`):**
        *   `async def identify_strategies_for_account_positions(db: Session, account_id: int) -> List[IdentifiedStrategyResult]:`
            *   Fetches open positions for an account.
            *   Groups positions by underlying and potentially expiration.
            *   Applies rule-based logic to each group to identify known strategies.
            *   Stores identified strategies by linking positions to predefined `StrategyDefinition` entries.
        *   `async def apply_strategy_rules_to_position_group(positions: List[Position]) -> Optional[StrategyDefinition]:` (Core rule engine).
        *   `async def create_custom_strategy(db: Session, user_id: int, account_id: int, strategy_in: CustomStrategyCreateSchema) -> CustomStrategyReadSchema:`
        *   `async def link_trades_to_strategy(db: Session, strategy_id: int, trade_ids: List[int]):`
    2.  **Database Models (`app/db/models/strategy.py`, enhance `Position`/`Transaction`):**
        *   `StrategyDefinition(Base)`: `id`, `name` (e.g., "Iron Condor"), `type` (enum: PREDEFINED, USER_CUSTOM), `description`, `rules_json` (optional, for complex predefined rules), `user_id` (nullable, for custom strategies).
        *   `TradeStrategyLink(Base)`: `trade_id` (FK to Transaction), `strategy_definition_id` (FK), `user_id`.
        *   `PositionGroupStrategyLink(Base)`: `strategy_definition_id` (FK), `user_id`, and a way to define the group of positions (e.g., store a unique hash of involved position IDs, or link to a temporary `PositionGroup` table).
    3.  **CRUD Operations (`app/crud/crud_strategy.py`):**
        *   For `StrategyDefinition` (creating custom, fetching predefined, listing user's custom).
        *   For `TradeStrategyLink` / `PositionGroupStrategyLink`.
    4.  **API Endpoints (`app/api/v1/endpoints/strategies.py`):** Implement as per API Relationships.
    5.  **Integration with Data Sync (Feature 2):**
        *   After new positions/trades are synced, the `StrategyService.identify_strategies_for_account_positions` can be triggered (possibly as a subsequent background task) to automatically tag them.
*   **Frontend (Next.js):**
    1.  **Displaying Strategies:** In position tables or trade detail views, show the `strategy_name`.
    2.  **Custom Strategy Management UI (`src/app/(dashboard)/strategies/page.tsx` - new):**
        *   Interface to view, create, edit, and delete custom strategies.
        *   Mechanism to select trades/positions (e.g., from a table) and assign them to a new or existing custom strategy.
    3.  **API Service Calls (`src/services/strategyService.ts` - new):** Functions for all strategy-related backend interactions.

**Pseudocode Example (Simplified Strategy Rule - Vertical Spread):**

```python
# In app/services/strategy_service.py (conceptual part of rule engine)

def check_for_vertical_spread(legs: List[Position]) -> Optional[str]:
    if len(legs) != 2: return None

    # Sort by strike to make comparisons easier (assuming legs are for same underlying & expiration)
    sorted_legs = sorted(legs, key=lambda p: p.option_strike_price)
    leg1, leg2 = sorted_legs[0], sorted_legs[1]

    # Must be same option type (both calls or both puts)
    if leg1.option_type != leg2.option_type or leg1.option_type is None:
        return None

    # Must have one long and one short position with same absolute quantity
    if not ((leg1.quantity > 0 and leg2.quantity < 0) or (leg1.quantity < 0 and leg2.quantity > 0)):
        return None
    if abs(leg1.quantity) != abs(leg2.quantity):
        return None

    # Determine if debit or credit (simplified)
    # Long Call Spread (Debit): Buy lower strike call, Sell higher strike call
    # Short Call Spread (Credit): Sell lower strike call, Buy higher strike call
    # Long Put Spread (Debit): Buy higher strike put, Sell lower strike put
    # Short Put Spread (Credit): Sell higher strike put, Buy lower strike put

    spread_type = ""
    if leg1.option_type == "CALL":
        if leg1.quantity > 0: # Long lower strike call
            spread_type = "Long Call Vertical Spread (Debit)"
        else: # Short lower strike call
            spread_type = "Short Call Vertical Spread (Credit)"
    elif leg1.option_type == "PUT":
        # For puts, leg1 is lower strike. Long Put Spread = Buy Higher, Sell Lower
        if leg2.quantity > 0: # Long higher strike put
            spread_type = "Long Put Vertical Spread (Debit)"
        else: # Short higher strike put
            spread_type = "Short Put Vertical Spread (Credit)"
            
    return spread_type if spread_type else "Vertical Spread"

# ... other rules for straddles, strangles, iron condors etc. ...
```
This feature adds significant analytical value by allowing users to track performance and risk by strategy, moving beyond individual positions.

