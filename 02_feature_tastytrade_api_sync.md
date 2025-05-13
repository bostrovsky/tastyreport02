# Feature 2: TastyTrade API Integration & Data Synchronization

**Feature Goal:**
To reliably, securely, and scalably synchronize the user's TastyTrade account data (transactions, positions, balances, and other relevant information) with the application's database. This includes an initial full historical sync and subsequent incremental updates to keep the data current, designed to support hundreds to thousands of users with good performance and reliability.

**API Relationships:**

*   **Backend API Endpoints (FastAPI - `/api/v1/`):**
    *   `POST /tastytrade-accounts/link`: (To initiate linking a TastyTrade account and store credentials securely for backend use).
        *   Request Body Schema: `TastyTradeCredentialsSchema` (e.g., API username/email, password. MFA/OTP to be handled interactively if possible, or instructions provided to user for session token retrieval if direct MFA automation is not feasible/secure).
        *   Response: `TastyTradeAccountReadSchema` (confirming linked account details, excluding sensitive info).
    *   `GET /tastytrade-accounts`: (List linked TastyTrade accounts for the user).
        *   Response Schema: `List[TastyTradeAccountReadSchema]`.
    *   `DELETE /tastytrade-accounts/{account_db_id}`: (To unlink a TastyTrade account and remove associated credentials).
    *   `POST /sync/tastytrade/{account_db_id}/trigger`: (To manually trigger a sync for a specific linked account).
        *   Request: Requires authenticated user, `account_db_id` path parameter.
        *   Response: `SyncTaskStatusSchema` (e.g., task ID, initial status).
    *   `GET /sync/status/{task_id}`: (To check the status of a specific sync background task).
        *   Response Schema: `SyncTaskStatusSchema` (e.g., `status` (pending, in_progress, completed, failed, retrying), `progress_percentage`, `details`, `last_updated`, `error_message`).
*   **External API:** TastyTrade API (utilizing the `tastytrade` Python library or direct, well-managed HTTP calls).
*   **Internal Logic:** Robust background task system (e.g., Celery with RabbitMQ/Redis broker and Flower for monitoring, or ARQ) for performing all synchronization operations asynchronously and reliably.

**Detailed Feature Requirements:**

1.  **Secure TastyTrade Account Linking & Credential Management:**
    *   Users must be able to securely provide their TastyTrade API credentials. These credentials should ideally be used by the backend only to obtain a session token.
    *   **Session Token Management:** The application must obtain a session token from TastyTrade. This token, not the raw credentials, should be stored securely (encrypted at rest using strong encryption like AES-256, associated with the user and their TastyTrade account number) and used for subsequent API calls.
    *   **Credential Encryption:** If raw credentials need to be temporarily held for token generation, they must be encrypted in transit and handled with extreme care, then securely discarded post-token generation.
    *   Handle multi-factor authentication (MFA/OTP) if required by TastyTrade. This might involve prompting the user for an OTP during the linking process if the TastyTrade API supports a flow for this, or guiding the user to generate a long-lived token if that's an option provided by TastyTrade for third-party app integrations.
    *   Support linking multiple TastyTrade accounts per application user.
    *   Provide functionality to unlink accounts and securely delete associated stored tokens/credentials.
2.  **Comprehensive Data Synchronization Scope:**
    *   **Transactions:** Fetch all historical and new transactions (trades, fees, cash movements, assignments, expirations, dividends, interest, etc.). Ensure all relevant fields from `sync.py` and TastyTrade API are captured (e.g., `transaction-id`, `transaction-type`, `transaction-sub-type`, `symbol`, `underlying-symbol`, `quantity`, `price`, `commission`, `fees`, `transaction-date`, `executed-at`, `order-id`).
    *   **Positions:** Fetch current open positions, including detailed leg information for options (strike, type, expiration) and greeks (delta, gamma, theta, vega, IV) if available directly or calculable.
    *   **Account Balances:** Fetch key account balances (net liquidity, cash balance, buying power, maintenance margin, option buying power, day trades left, etc.) and historical balance snapshots if possible.
    *   **Orders:** Fetch historical and current open/working orders, including status, type, price, quantity.
    *   **Watchlists (Optional Future):** Sync user's TastyTrade watchlists.
3.  **Robust Synchronization Mechanisms:**
    *   **Initial Full Sync:** Upon linking a new account, trigger a comprehensive full sync of all historical transactions, orders, and current positions/balances. This should be a clearly communicated, potentially long-running background task.
    *   **Incremental/Scheduled Sync:** Implement scheduled background tasks (e.g., configurable, but perhaps every 1-4 hours, and a more intensive sync daily after market close) to fetch new transactions, orders, and update positions/balances. Use watermarking (last fetched transaction ID/timestamp) to optimize incremental syncs.
    *   **Real-time/Webhook (If TastyTrade Supports):** Explore if TastyTrade offers webhooks for near real-time updates on trades/orders. This would be an enhancement for responsiveness.
    *   **Manual Sync Trigger:** Allow users to manually trigger a sync for their account(s), with appropriate rate limiting to prevent abuse.
4.  **Scalable & Reliable Background Task Execution:**
    *   Utilize a robust task queue system (e.g., Celery with multiple workers, or ARQ) to handle synchronization tasks asynchronously.
    *   Design tasks to be idempotent where possible (retrying a task multiple times yields the same result).
    *   Implement retry mechanisms with exponential backoff for transient errors (network issues, temporary API unavailability).
    *   Monitor task queue health and performance (e.g., queue length, task failure rates).
5.  **Efficient Data Storage & Integrity (Supabase/PostgreSQL):**
    *   Define optimized database schemas for transactions, positions, orders, balances, etc., with appropriate indexing for query performance.
    *   Ensure data integrity: use unique constraints (e.g., `tastytrade_transaction_id`), handle updates to existing records (e.g., position updates, order status changes) correctly using UPSERT logic or checks.
    *   Store timestamps for data creation and updates (`created_at`, `updated_at`).
6.  **Comprehensive Error Handling, Logging & Monitoring:**
    *   Implement detailed logging for all sync operations, including API calls, data processing steps, and errors.
    *   Gracefully handle API errors from TastyTrade (e.g., invalid session, rate limits, specific error codes) and translate them into actionable information or retry strategies.
    *   If a session token expires, attempt to re-authenticate automatically using stored (encrypted) credentials if that flow is supported and secure, or notify the user if re-linking is required.
    *   Provide clear feedback to the user regarding sync status and any persistent errors.
    *   Implement monitoring and alerting for critical sync failures or performance degradation.
7.  **Security (Reiteration & Expansion):**
    *   All sensitive data (API keys, session tokens) must be encrypted at rest (e.g., AES-256 GCM) and in transit (HTTPS).
    *   Regularly review and update security practices for credential handling.
    *   Minimize the attack surface by only requesting necessary permissions/scopes from TastyTrade if applicable.
8.  **Performance Optimization:**
    *   Optimize API calls to TastyTrade: use pagination effectively, request only necessary fields, respect rate limits.
    *   Batch database operations (inserts/updates) where appropriate to reduce load.
    *   Design background tasks to be efficient and avoid unnecessary computations.
9.  **Testing Strategy:**
    *   **Unit Tests:** For individual functions within services (e.g., data transformation, specific API call logic - mocked).
    *   **Integration Tests:** Test interaction between services, database, and mocked TastyTrade API. Test sync logic for various scenarios (initial sync, incremental sync, error cases).
    *   **End-to-End Tests (Staging/QA):** If possible, test against a TastyTrade paper trading account or a dedicated test account.

**Detailed Implementation Guide:**

*   **Backend (FastAPI):**
    1.  **TastyTrade Service (`app/services/tastytrade_service.py`):**
        *   Robust wrapper for the `tastytrade` library or direct HTTP client.
        *   Methods for all required API interactions: login/session management, fetching accounts, transactions (with pagination and date filters), positions, balances, orders.
        *   Handles API-specific error parsing and rate limit awareness.
        *   Manages the active session token for an account.
    2.  **Sync Orchestration Service (`app/services/sync_service.py`):**
        *   `async def trigger_account_sync(user_id: int, account_db_id: int, sync_type: str = "incremental") -> SyncTaskStatusSchema:` Dispatches background task.
        *   `async def get_sync_task_status(task_id: str) -> SyncTaskStatusSchema:` Retrieves status from task queue backend.
    3.  **Background Tasks (`app/background_tasks/tastytrade_sync_tasks.py`):**
        *   `sync_account_full(account_db_id: int)`: Task for initial full sync.
        *   `sync_account_incremental(account_db_id: int)`: Task for regular incremental syncs.
        *   These tasks will use `TastyTradeService` to fetch data and `CRUD` operations to store it. They will update a persistent record of their progress/status.
        *   Implement locking mechanisms if needed to prevent concurrent syncs for the same account.
    4.  **Database Models (`app/db/models/`):**
        *   `TastyTradeAccount`: `id`, `user_id`, `account_number`, `encrypted_tastytrade_session_token`, `token_expires_at`, `last_sync_status` (enum: PENDING, RUNNING, SUCCESS, FAILED, NEEDS_REAUTH), `last_successful_sync_at`, `last_transaction_watermark` (timestamp or ID).
        *   `Transaction`, `Position`, `Order`, `AccountBalanceSnapshot` (with timestamp).
    5.  **CRUD Operations (`app/crud/`):**
        *   Specific CRUD modules for each model, with methods for efficient batch creation/update and duplicate handling (e.g., `create_transactions_batch`, `upsert_positions_batch`).
    6.  **Schemas (`app/schemas/`):**
        *   `TastyTradeCredentialsSchema`, `TastyTradeAccountReadSchema`, `TastyTradeAccountCreateSchema`.
        *   `TransactionSchema`, `PositionSchema`, `OrderSchema`, `AccountBalanceSchema` (for API and internal use, possibly with `...Create`, `...Update`, `...Read` variants).
        *   `SyncTaskStatusSchema`.
    7.  **API Endpoints (`app/api/v1/endpoints/tastytrade_accounts.py`, `app/api/v1/endpoints/sync.py`):** Implement as per API Relationships.
*   **Frontend (Next.js):**
    1.  **Account Linking UI (`src/app/(dashboard)/settings/accounts/page.tsx`):** Secure form for credentials, calls backend, displays status, lists linked accounts with sync status and manual trigger.
    2.  **API Service Calls (`src/services/tastytradeService.ts`, `src/services/syncService.ts`):** Functions for all backend interactions.

**Pseudocode Example (Incremental Sync Task Snippet):**

```python
# In app/background_tasks/tastytrade_sync_tasks.py (conceptual)

async def sync_account_incremental_task(ctx, account_db_id: int):
    db = await get_db_session_for_task()
    sync_log = # Get/create a sync log entry for this task instance
    try:
        tt_account = await crud_tastytrade_account.get(db, id=account_db_id)
        if not tt_account or not tt_account.encrypted_tastytrade_session_token:
            await update_sync_log(sync_log, status="FAILED", message="Account or token not found")
            return

        session_token = await decrypt_token(tt_account.encrypted_tastytrade_session_token)
        tasty_service = TastyTradeService(session_token=session_token)

        # Check token validity, refresh if necessary and possible
        if not await tasty_service.is_session_valid():
            # Attempt re-login or mark account as NEEDS_REAUTH
            await update_sync_log(sync_log, status="NEEDS_REAUTH", message="Session expired")
            await crud_tastytrade_account.update_status(db, tt_account, "NEEDS_REAUTH")
            return

        await update_sync_log(sync_log, status="RUNNING", details="Fetching new transactions...")
        new_transactions = await tasty_service.get_transactions(
            account_number=tt_account.account_number,
            start_date=tt_account.last_transaction_watermark
        )
        if new_transactions:
            await crud_transaction.create_transactions_batch(db, account_id=tt_account.id, transactions_data=new_transactions)
            new_watermark = get_latest_timestamp_from_transactions(new_transactions)
            await crud_tastytrade_account.update_watermark(db, tt_account, new_watermark)

        await update_sync_log(sync_log, details="Fetching current positions...")
        current_positions = await tasty_service.get_positions(account_number=tt_account.account_number)
        await crud_position.upsert_positions_batch(db, account_id=tt_account.id, positions_data=current_positions)

        # ... fetch balances, orders ...

        await crud_tastytrade_account.update_sync_info(db, tt_account, status="SUCCESS", last_sync_at=datetime.utcnow())
        await update_sync_log(sync_log, status="SUCCESS")

    except TastyTradeAPIError as e:
        # Log specific API error, decide if retryable
        await update_sync_log(sync_log, status="FAILED", message=f"API Error: {e}")
        # Potentially schedule retry based on error type
    except Exception as e:
        # Log generic error
        await update_sync_log(sync_log, status="FAILED", message=f"Internal Error: {e}")
    finally:
        await db.close()
```
This feature is foundational and complex, requiring careful attention to security, reliability, and data accuracy to build user trust and support the application's core functionality.
