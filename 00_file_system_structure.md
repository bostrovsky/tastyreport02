# File System Structure for TastyTrade Tracker

This document outlines the proposed file system structure for both the backend (FastAPI) and frontend (Next.js) components of the TastyTrade Tracker application.

## Backend (FastAPI) File Structure

The backend will be built using FastAPI. A modular structure is proposed for better organization and maintainability.

```
/app/
|-- api/
|   |-- __init__.py
|   |-- v1/
|   |   |-- __init__.py
|   |   |-- endpoints/
|   |   |   |-- __init__.py
|   |   |   |-- auth.py         # Authentication routes (login, logout, register)
|   |   |   |-- users.py        # User management routes (if any beyond auth)
|   |   |   |-- accounts.py     # TastyTrade account linking, management
|   |   |   |-- sync.py         # Data synchronization triggers, status
|   |   |   |-- reports.py      # P&L, metrics, and other report generation
|   |   |   |-- views.py        # Data for tabbed views (calendar, underlying, etc.)
|   |   |   |-- market_data.py  # Market data endpoints
|   |   |   |-- strategies.py   # Strategy identification and management
|   |   |-- deps.py           # FastAPI dependencies (e.g., get_current_user)
|   |-- router.py             # Main API router including v1
|-- background_tasks/
|   |-- __init__.py
|   |-- tastytrade_sync.py    # Celery/ARQ tasks for TastyTrade data sync
|   |-- market_data_fetch.py  # Tasks for fetching market data
|-- core/
|   |-- __init__.py
|   |-- config.py             # Application configuration (settings, secrets)
|   |-- security.py           # Password hashing, JWT handling
|   |--celery_app.py        # Celery app definition (if using Celery)
|   |--arq_app.py           # ARQ app definition (if using ARQ)
|-- crud/                     # Create, Read, Update, Delete operations
|   |-- __init__.py
|   |-- crud_user.py
|   |-- crud_account.py
|   |-- crud_transaction.py
|   |-- crud_position.py
|   |-- crud_strategy.py
|   |-- base.py               # Base CRUD class
|-- db/
|   |-- __init__.py
|   |-- base_class.py         # SQLAlchemy base model
|   |-- models/               # SQLAlchemy models (e.g., user.py, account.py, transaction.py)
|   |   |-- __init__.py
|   |   |-- user.py
|   |   |-- tastytrade_account.py
|   |   |-- transaction.py
|   |   |-- position.py
|   |   |-- strategy.py
|   |   |-- market_data_entry.py
|   |-- session.py            # Database session management (SQLAlchemy)
|-- schemas/                  # Pydantic schemas for data validation and serialization
|   |-- __init__.py
|   |-- user.py
|   |-- token.py
|   |-- tastytrade_account.py
|   |-- transaction.py
|   |-- position.py
|   |-- report.py             # Schemas for P&L, metrics reports
|   |-- view.py               # Schemas for tabbed views data
|   |-- market_data.py
|   |-- strategy.py
|-- services/                 # Business logic layer
|   |-- __init__.py
|   |-- tastytrade_service.py # Logic for interacting with TastyTrade API
|   |-- sync_service.py       # Orchestrates data synchronization
|   |-- pnl_service.py        # P&L calculation logic
|   |-- reporting_service.py  # Logic for generating reports and view data
|   |-- market_data_service.py # Logic for fetching/managing market data
|   |-- strategy_service.py   # Logic for strategy identification
|-- tests/                    # Unit and integration tests
|   |-- __init__.py
|   |-- api/
|   |-- crud/
|   |-- services/
|   |-- utils/
|   |-- conftest.py           # Pytest fixtures
|-- main.py                   # FastAPI application entry point
|-- requirements.txt          # Python dependencies
|-- Dockerfile                # Docker configuration for backend
|-- .env.example              # Environment variable template
```

## Frontend (Next.js) File Structure

The frontend will be built using Next.js with the App Router.

```
/frontend/  (or /src/ if preferred as root for Next.js project)
|-- public/                   # Static assets (images, fonts, etc.)
|   |-- favicon.ico
|-- src/
|   |-- app/                  # Next.js App Router
|   |   |-- (auth)/           # Route group for authentication pages
|   |   |   |-- login/
|   |   |   |   |-- page.tsx
|   |   |   |-- register/     # If self-registration is supported
|   |   |   |   |-- page.tsx
|   |   |-- (dashboard)/      # Route group for authenticated dashboard pages
|   |   |   |-- layout.tsx    # Layout for dashboard including sidebar/navbar
|   |   |   |-- page.tsx      # Main dashboard overview
|   |   |   |-- calendar/
|   |   |   |   |-- page.tsx
|   |   |   |-- underlying/
|   |   |   |   |-- page.tsx
|   |   |   |-- strategy/
|   |   |   |   |-- page.tsx
|   |   |   |-- pnl-by-delta/
|   |   |   |   |-- page.tsx
|   |   |   |-- net-liquidity/
|   |   |   |   |-- page.tsx
|   |   |   |-- settings/     # User settings, account management
|   |   |   |   |-- page.tsx
|   |   |-- globals.css       # Global styles
|   |   |-- layout.tsx        # Root layout
|   |-- components/           # Reusable UI components
|   |   |-- ui/               # Base UI elements (Button, Input, Card - often from shadcn/ui)
|   |   |-- charts/           # Chart components (e.g., using Recharts)
|   |   |-- dashboard/        # Components specific to dashboard sections
|   |   |-- auth/             # Authentication-related components (LoginForm)
|   |   |-- views/            # Components for specific tabbed views
|   |   |   |-- CalendarGrid.tsx
|   |   |   |-- UnderlyingTable.tsx
|   |   |   |-- NetLiquidityStatement.tsx
|   |-- contexts/             # React Context API for global state (or Zustand/Redux store)
|   |   |-- AuthContext.tsx
|   |   |-- ThemeContext.tsx
|   |-- hooks/                # Custom React hooks
|   |   |-- useAuth.ts
|   |   |-- useApi.ts         # Hook for making API calls
|   |-- lib/                  # Utility functions, constants, helper modules
|   |   |-- utils.ts          # General utility functions
|   |   |-- constants.ts
|   |   |-- formatDate.ts
|   |-- services/             # API service functions for fetching data from backend
|   |   |-- authService.ts
|   |   |-- reportService.ts
|   |   |-- marketDataService.ts
|   |   |-- tastytradeAccountService.ts
|   |-- styles/               # Additional global styles or theme configuration
|   |-- types/                # TypeScript type definitions
|   |   |-- index.ts
|   |   |-- api.ts            # Types for API request/response payloads
|-- tests/                    # Frontend tests (Jest, React Testing Library, Cypress/Playwright)
|   |-- __mocks__/
|   |-- components/
|   |-- e2e/                  # End-to-end tests
|-- .env.local.example        # Environment variable template for frontend
|-- next.config.js            # Next.js configuration
|-- tsconfig.json             # TypeScript configuration
|-- package.json              # Project dependencies and scripts
|-- postcss.config.js         # PostCSS configuration (for Tailwind CSS)
|-- tailwind.config.js        # Tailwind CSS configuration
```
