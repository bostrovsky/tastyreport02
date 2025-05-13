# TastyTrade Tracker – MVP PRD & Roadmap

## 0. Key Decisions & Constraints

- **Self-registration**: Required for MVP.
- **Tastytrade API**: Credentials and test account available; integration will follow best practices and your `sync.py` approach.
- **Market Data**: Use Marketstack.com for real-time/near-real-time data, supplementing Tastytrade.
- **Hosting**: **Vercel** is recommended for the frontend (Next.js) and can also host serverless FastAPI endpoints (via Vercel Serverless Functions or Vercel + Supabase for DB). For heavier backend (background jobs), consider **Railway** or **Render** for FastAPI + Celery/ARQ + Redis/Postgres. Both are scalable, secure, and affordable.
- **Payments**: Stripe integration, 30-day free trial, $5/mo or $50/year, cancel anytime.
- **Scale**: MVP targets ≤100 users.
- **Data Retention**: Store current and prior year.
- **Testing**: High coverage/unit/integration, E2E not required but recommended for critical flows.
- **Design**: Stripe, Scale, ClickUp as inspiration; modern, clean, responsive.
- **Reports**: Flexible for MVP.

---

## 1. Feature Breakdown, Risks, Mitigation, Dependencies, Resources, Priority, Estimates, Success, Testing, Deployment

### 1. User Authentication & Self-Registration

**Tasks:**
- FastAPI endpoints: `/register`, `/login`, `/logout`, `/refresh-token`, `/me`
- Email verification (optional for MVP, but recommended for abuse prevention)
- JWT/refresh token logic, password hashing (Argon2id)
- Frontend: Registration/login forms, AuthContext, protected routes
- Stripe onboarding: Free trial logic, subscription status check

**Risks:**  
- **High**: Security (token leaks, brute-force, registration spam)
- **Medium**: Stripe integration edge cases

**Mitigation:**  
- Use `passlib[argon2]`, `python-jose`, `slowapi` for rate limiting, email verification (SendGrid or similar, optional)
- Stripe test mode, webhook validation, trial logic in backend

**Dependencies:** None

**Resources:** 1 backend, 1 frontend

**Priority:** Must-have

**Estimate:** 6 days

**Success Criteria:**  
- Secure, frictionless registration/login/logout, trial logic, Stripe status reflected in UI

**Testing:**  
- Unit: password, JWT, endpoints  
- Integration: registration, login, Stripe webhooks  
- E2E: registration, login, trial, subscribe, cancel

---

### 2. Tastytrade API Integration & Data Sync

**Tasks:**
- Async Tastytrade session (see `sync.py`), MFA handling (prompt user if needed)
- Secure credential/session token storage (encrypted at rest)
- Background sync (Celery/ARQ), deduplication (see `sync.py` logic)
- Data models: transactions, positions, balances, orders
- Manual sync trigger, sync status API
- Marketstack.com integration for real-time quotes

**Risks:**  
- **High**: Tastytrade API changes, MFA, credential security, sync reliability  
- **High**: Deduplication, data integrity

**Mitigation:**  
- Use your deduplication window logic, unique constraints, robust error handling, log all syncs
- MFA: If required, prompt user for OTP, fallback to session token if possible

**Dependencies:** Auth

**Resources:** 2 backend, 1 infra/devops

**Priority:** Must-have

**Estimate:** 10 days

**Success Criteria:**  
- Reliable sync, no data loss/duplication, user can see up-to-date trades/positions

**Testing:**  
- Unit: API wrappers, data transforms  
- Integration: sync flows, error cases, deduplication  
- E2E: link account, trigger sync, view data

---

### 3. Market Data Integration (Marketstack.com)

**Tasks:**
- Marketstack API integration (indices, quotes)
- Caching (Redis), background fetch task
- API endpoint for dashboard
- Frontend widget for market indices

**Risks:**  
- **Medium**: API quota/rate limits, data staleness

**Mitigation:**  
- Use Redis cache, fallback to stale data, monitor API usage

**Dependencies:** None

**Resources:** 1 backend, 1 frontend

**Priority:** Must-have

**Estimate:** 3 days

**Success Criteria:**  
- Market data always available, up-to-date within 5 minutes, clear error states

**Testing:**  
- Unit: API parsing, cache logic  
- Integration: background fetch, cache expiry  
- E2E: dashboard display

---

### 4. Dashboard

**Tasks:**
- Backend: Aggregated dashboard endpoint (P&L, metrics, market data)
- Frontend: Dashboard layout, widgets (P&L, metrics, market, account selector)
- State management for dashboard data

**Risks:**  
- **Medium**: Data aggregation performance, stale data, UX complexity

**Mitigation:**  
- Optimize queries, cache aggregates, loading states in UI

**Dependencies:** Auth, Data Sync, Market Data

**Resources:** 1 backend, 1 frontend

**Priority:** Must-have

**Estimate:** 5 days

**Success Criteria:**  
- Loads in <2s, accurate data, responsive UI

**Testing:**  
- Unit: aggregation logic  
- Integration: endpoint, data freshness  
- E2E: dashboard load, account switch

---

### 5. P&L Calculation & Reporting

**Tasks:**
- Realized/unrealized P&L logic (FIFO, options, fees)
- API endpoints for summary, by underlying, by trade
- Frontend: P&L display components

**Risks:**  
- **High**: Calculation accuracy, edge cases (assignments, expirations)
- **Medium**: Performance for large datasets

**Mitigation:**  
- Extensive test vectors, compare with broker, optimize queries

**Dependencies:** Data Sync

**Resources:** 2 backend, 1 frontend

**Priority:** Must-have

**Estimate:** 7 days

**Success Criteria:**  
- Matches broker P&L within 1%, handles all trade types

**Testing:**  
- Unit: calculation logic, edge cases  
- Integration: API, large data  
- E2E: user views P&L

---

### 6. Portfolio Metrics Calculation & Display

**Tasks:**
- Metrics aggregation (delta, theta, net liq, BP)
- API endpoint for metrics
- Frontend: metrics widgets

**Risks:**  
- **Medium**: Greek calculation (if not provided), data freshness

**Mitigation:**  
- Use broker-provided Greeks for MVP, mark as N/A if missing

**Dependencies:** Data Sync

**Resources:** 1 backend, 1 frontend

**Priority:** Must-have

**Estimate:** 3 days

**Success Criteria:**  
- Metrics match broker, always up-to-date

**Testing:**  
- Unit: aggregation, fallback logic  
- Integration: endpoint, data sync  
- E2E: metrics display

---

### 7. Strategy Identification & Management

**Tasks:**
- Rule-based strategy engine (verticals, condors, etc.)
- Custom strategy tagging (user-defined)
- API endpoints for strategies
- Frontend: display strategy names, custom strategy UI

**Risks:**  
- **High**: Rule complexity, ambiguous cases, user confusion
- **Medium**: Performance for large portfolios

**Mitigation:**  
- Start with simple, unambiguous strategies, allow user override, optimize grouping

**Dependencies:** Data Sync, P&L

**Resources:** 2 backend, 1 frontend

**Priority:** Should-have

**Estimate:** 7 days

**Success Criteria:**  
- 90%+ of common strategies auto-identified, user can tag custom

**Testing:**  
- Unit: rule engine, edge cases  
- Integration: API, tagging  
- E2E: user tags/edits strategies

---

### 8. Tabbed Views (Calendar, Underlying, Strategy, P&L by Delta)

**Tasks:**
- Backend: Aggregation endpoints for each view
- Frontend: Tabbed navigation, data tables, charts

**Risks:**  
- **Medium**: Query performance, data consistency, UI complexity

**Mitigation:**  
- Pre-aggregate where possible, paginate, loading states

**Dependencies:** Data Sync, P&L, Strategy

**Resources:** 1 backend, 2 frontend

**Priority:** Should-have

**Estimate:** 6 days

**Success Criteria:**  
- All views load in <2s, correct data, smooth navigation

**Testing:**  
- Unit: aggregation, filters  
- Integration: endpoints, tab switching  
- E2E: user explores all views

---

### 9. Net Liquidity Tab

**Tasks:**
- Backend: Net liquidity reconciliation logic, endpoint
- Frontend: Reconciliation view

**Risks:**  
- **Medium**: Data completeness (historical net liq), edge cases

**Mitigation:**  
- Fallback to calculated values, clear error messages

**Dependencies:** Data Sync, P&L

**Resources:** 1 backend, 1 frontend

**Priority:** Should-have

**Estimate:** 3 days

**Success Criteria:**  
- Reconciliation matches broker, all components explained

**Testing:**  
- Unit: calculation, edge cases  
- Integration: endpoint, data sync  
- E2E: user views reconciliation

---

### 10. Subscription Management (Stripe)

**Tasks:**
- Stripe integration (checkout, webhooks, trial logic)
- Subscription model, user roles
- API endpoints for subscription status
- Frontend: subscription UI, plan selection, trial/cancel logic

**Risks:**  
- **Medium**: Payment errors, access control

**Mitigation:**  
- Use Stripe hosted checkout, test webhooks, role-based access

**Dependencies:** Auth

**Resources:** 1 backend, 1 frontend

**Priority:** Must-have

**Estimate:** 4 days

**Success Criteria:**  
- Users can subscribe, access is gated, payments processed

**Testing:**  
- Unit: webhook handling  
- Integration: payment flow  
- E2E: subscribe, access features

---

## 2. Dependency Mapping

- **Auth** → All features
- **Data Sync** → P&L, Metrics, Strategy, Tabbed Views, Net Liq
- **Market Data** → Dashboard, Metrics
- **P&L** → Dashboard, Tabbed Views, Net Liq
- **Strategy** → Tabbed Views
- **Subscription** → Access control for all features

---

## 3. Resource Requirements

- **Backend**: 2 engineers (core API, sync, P&L, strategy)
- **Frontend**: 2 engineers (Next.js, UI, state, API integration)
- **Infra/DevOps**: 1 (setup, CI/CD, monitoring)
- **QA**: 1 (manual + automated test writing)
- **Product/Design**: 1 (requirements, UI/UX review)

---

## 4. Time Estimates

- **Total (Must-have)**: ~38 days (with some parallelization)
- **Should-have**: +16 days
- **Buffer**: +5 days (integration, bugfix, polish)
- **Overall**: ~59 days (2–3 months for MVP, with overlap)

---

## 5. Success Criteria (Per Feature)

- **Auth**: Secure, frictionless login/registration, no breaches, 100% test pass
- **Data Sync**: 99%+ reliability, no data loss, user can always see up-to-date data
- **Market Data**: <5min lag, always available, clear errors
- **Dashboard**: Loads in <2s, accurate, actionable info
- **P&L**: Matches broker, handles all trade types, no calculation errors
- **Metrics**: Accurate, up-to-date, matches broker
- **Strategy**: 90%+ auto-identification, user can override
- **Tabbed Views**: All views performant, correct, easy to use
- **Net Liq**: Reconciliation matches broker, all components explained
- **Subscription**: No access leaks, payments processed, clear UI

---

## 6. Testing Requirements

- **Unit**: All core logic (auth, sync, P&L, strategy, metrics)
- **Integration**: API endpoints, background tasks, data flows
- **E2E**: User flows (login, sync, dashboard, tabbed views, subscription)
- **Performance**: Load tests for sync, dashboard, tabbed views
- **Security**: Penetration test, dependency audit

---

## 7. Deployment Strategy

- **Environments**: 
  - **Local**: For dev, with mock/test data
  - **Staging**: Full stack, real APIs, test accounts, CI/CD deploy, feature flags
  - **Production**: Hardened, monitored, backups, alerting

- **CI/CD**: 
  - Lint, type-check, test, build, deploy (GitHub Actions, Vercel, etc.)
  - Automated rollback on failure

- **Secrets Management**: 
  - Use environment variables, never commit secrets

- **Monitoring**: 
  - Error tracking (Sentry), performance (APM), background task health

- **Data Backups**: 
  - Nightly DB and Redis backups

---

## 8. Data Model Overview

- **User**: id, email, hashed_password, role, is_active, created_at, last_login_at, subscription_status, stripe_customer_id
- **TastyTradeAccount**: id, user_id, account_number, encrypted_session_token, last_sync_status, last_sync_at
- **Transaction**: id, account_id, tastytrade_id, type, symbol, underlying, quantity, price, commission, fees, date, executed_at, order_id
- **Position**: id, account_id, symbol, underlying, quantity, open_price, current_price, delta, theta, vega, expiration, type, last_updated_at
- **StrategyDefinition**: id, name, type (auto/custom), description, rules_json, user_id (nullable)
- **StrategyLink**: id, strategy_id, position_id or transaction_id, user_id
- **AccountBalanceSnapshot**: id, account_id, net_liquidity, buying_power, timestamp
- **Subscription**: id, user_id, status, stripe_id, plan, started_at, ended_at
- **ReportTemplate**: id, user_id, name, config_json

---

## 9. API Integration Focus

- **OAuth**: For TastyTrade, use secure credential flow, handle MFA, store only session tokens
- **Data Sync**: Full/incremental, idempotent, deduplication via unique constraints, upsert logic (see `sync.py`)
- **Error Handling**: All API errors logged, user-friendly messages, retry logic for transient errors
- **Rate Limiting**: Respect TastyTrade and Marketstack limits, exponential backoff, alert on approaching limits

---

## 10. Initial Steps (Tech/Infra Readiness)

1. **Verify access to:**
   - TastyTrade API (test account, credentials, MFA flow)
   - Marketstack.com API key
   - Vercel (frontend, serverless backend), Railway/Render (backend, background jobs)
   - Database (Postgres/Supabase), Redis (for cache, background tasks)
   - Stripe (test mode)

2. **Setup:**
   - Python 3.11+ virtual environment, install FastAPI, Celery/ARQ, SQLAlchemy, passlib[argon2], python-jose, httpx, Redis client
   - Node.js 20+, Next.js 15, React 19, Tailwind, Shadcn UI, Radix UI, Axios/SWR, Jest/Playwright
   - CI/CD pipeline (GitHub Actions or similar)
   - Secrets management (dotenv, Vercel/Netlify secrets, etc.)

3. **Smoke test:** 
   - Run FastAPI and Next.js locally, connect to DB, run a test background task, fetch market data

---

## 11. Roadmap Summary

- **Phase 1 (Weeks 1–2):** Auth, Data Model, Market Data, Initial Sync, Dashboard skeleton, Stripe onboarding
- **Phase 2 (Weeks 3–4):** Full Data Sync, P&L, Metrics, Core Tabbed Views
- **Phase 3 (Weeks 5–6):** Strategy Engine, Custom Tagging, Net Liq, Subscription polish
- **Phase 4 (Weeks 7–8):** Polish, Testing, Performance, Security, E2E, Staging/Prod Deploy

---

## 12. Early Risk Mitigation

- **MFA/Session Handling**: Build Tastytrade linking UI to prompt for OTP if needed, fallback to session token if possible.
- **Stripe**: Implement test mode, webhook validation, trial logic before launch.
- **Data Deduplication**: Use your `sync.py` windowed deduplication logic from day one.
- **API Quotas**: Monitor Marketstack and Tastytrade usage, alert on approaching limits.
- **Security**: Use strong password hashing, secure token storage, rate limiting, and regular dependency audits.

---

**Next Steps:**  
- Confirm access to all required APIs and services.
- Set up local and staging environments.
- Begin with user registration/auth, Stripe onboarding, and Tastytrade account linking.
- Prioritize early delivery of dashboard with real data to validate core value.

If you need detailed Tastytrade API integration instructions or code samples, I can provide a summary and best practices based on the latest public documentation and your `sync.py` approach. Let me know if you want this as a next step. 