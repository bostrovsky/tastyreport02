"""Tastytrade transaction synchronization module."""

import sys
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from postgrest import AsyncPostgrestClient
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from tastytrade import Account, Session

from config import Config

console = Console()

class TransactionSync:
    """Handles synchronization of Tastytrade transactions to Supabase."""

    def __init__(self) -> None:
        """Initialize the sync handler."""
        self.session: Optional[Session] = None
        self.postgrest: Optional[AsyncPostgrestClient] = None
        self.config = Config()

    async def connect(self) -> None:
        """Connect to both Tastytrade and Supabase."""
        if not self.config.is_valid:
            console.print("[red]Error:[/red] Missing required configuration.")
            sys.exit(1)

        # Connect to Tastytrade
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Connecting to Tastytrade...", total=None)
            self.session = Session(
                self.config.tasty_username,
                self.config.tasty_password,
                remember_me=True
            )

        # Connect to Supabase via Postgrest
        self.postgrest = AsyncPostgrestClient(
            base_url=f"{self.config.supabase_url}/rest/v1",
            headers={
                "apikey": self.config.supabase_key,
                "Authorization": f"Bearer {self.config.supabase_key}"
            }
        )

    async def get_last_sync_time(self, account_number: str) -> Optional[datetime]:
        """Get the timestamp of the last synced transaction for an account."""
        result = await self.postgrest.from_("transactions") \
            .select("executed_at") \
            .eq("account_number", account_number) \
            .order("executed_at", desc=True) \
            .limit(1) \
            .execute()

        if result.data and result.data[0]:
            return datetime.fromisoformat(result.data[0]["executed_at"])
        return None

    async def sync_transactions(self) -> None:
        """Synchronize transactions from Tastytrade to Supabase."""
        if not self.session or not self.postgrest:
            console.print("[red]Error:[/red] Not connected to services.")
            return

        # Fetch accounts using the correct async method
        accounts = await Account.a_get(self.session)

        for account in accounts:
            console.print(f"\nSyncing transactions for account {account.account_number}...")

            # Get last sync time
            last_sync = await self.get_last_sync_time(account.account_number)
            if last_sync:
                console.print(f"Last sync: {last_sync.isoformat()}")

            # Fetch transactions using the correct async method
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Fetching transactions...", total=None)
                transactions = await account.a_get_history(self.session)
                # No last_sync filter; rely on deduplication
                progress.update(task, completed=True)

            if not transactions:
                console.print("No new transactions found.")
                continue

            console.print(f"Found {len(transactions)} new transactions.")
            if transactions:
                first_txn = transactions[0]
                print("Sample transaction attributes:", dir(first_txn))
                print("Sample transaction as dict:", getattr(first_txn, '__dict__', str(first_txn)))

            # 1. Get the latest executed_at date for this account
            result = await self.postgrest.from_("transactions") \
                .select("executed_at") \
                .eq("account_number", account.account_number) \
                .order("executed_at", desc=True) \
                .limit(1) \
                .execute()
            if result.data and result.data[0]:
                latest_date = datetime.fromisoformat(result.data[0]["executed_at"]).date()
                # 2. Set window: from (latest_date - 5 days) to today
                start_date = latest_date - timedelta(days=5)
                end_date = date.today()
                # 3. Filter Tastytrade transactions in that window
                recent_trades = [
                    t for t in transactions
                    if t.executed_at and start_date <= t.executed_at.date() <= end_date
                ]
                # 4. Fetch all transaction_ids from the DB in that window
                db_result = await self.postgrest.from_("transactions") \
                    .select("transaction_id") \
                    .eq("account_number", account.account_number) \
                    .gte("executed_at", start_date.isoformat()) \
                    .lte("executed_at", end_date.isoformat()) \
                    .execute()
                existing_ids = set(str(row["transaction_id"]) for row in (db_result.data or []))
            else:
                # First sync: consider all transactions
                recent_trades = transactions
                existing_ids = set()

            # 5. Insert only trades whose transaction_id is not already present
            truly_new = [t for t in recent_trades if str(t.id) not in existing_ids]

            if not truly_new:
                console.print("No new transactions to insert.")
                continue

            console.print(f"Inserting {len(truly_new)} new transactions...")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Inserting transactions...", total=len(truly_new))
                for transaction in truly_new:
                    try:
                        await self.postgrest.from_("transactions").insert({
                            "account_number": account.account_number,
                            "transaction_id": transaction.id,
                            "transaction_type": getattr(transaction, "transaction_type", None),
                            "transaction_subtype": getattr(transaction, "transaction_sub_type", None),
                            "symbol": transaction.symbol,
                            "instrument_type": transaction.instrument_type,
                            "underlying_symbol": transaction.underlying_symbol,
                            "action": transaction.action,
                            "value": str(transaction.value) if transaction.value else None,
                            "price": str(transaction.price) if transaction.price else None,
                            "quantity": str(transaction.quantity) if transaction.quantity else None,
                            "commission": str(transaction.commission) if hasattr(transaction, "commission") and transaction.commission else None,
                            "regulatory_fees": str(transaction.regulatory_fees) if hasattr(transaction, "regulatory_fees") and transaction.regulatory_fees else None,
                            "clearing_fees": str(transaction.clearing_fees) if hasattr(transaction, "clearing_fees") and transaction.clearing_fees else None,
                            "proprietary_index_option_fees": str(transaction.proprietary_index_option_fees) if hasattr(transaction, "proprietary_index_option_fees") and transaction.proprietary_index_option_fees else None,
                            "other_charge": str(transaction.other_charge) if hasattr(transaction, "other_charge") and transaction.other_charge else None,
                            "multiplier": transaction.multiplier if hasattr(transaction, "multiplier") else None,
                            "executed_at": transaction.executed_at.isoformat() if transaction.executed_at else None,
                            "description": transaction.description
                        }).execute()
                        progress.advance(task)
                    except Exception as e:
                        console.print(f"[red]Error inserting transaction {transaction.id}:[/red] {str(e)}")
                        continue
            console.print("Sync completed.")

async def main() -> None:
    """Main entry point."""
    sync = TransactionSync()
    try:
        await sync.connect()
        await sync.sync_transactions()
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
