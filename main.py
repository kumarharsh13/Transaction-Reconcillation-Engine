
from models.transaction import (
    Transaction,
    CreditTransaction,
    DebitTransaction,
    TransactionStatus,
)
from services.processor import TransactionProcessor
from services.analytics import TransactionAnalytics

def main():
    # ──────────────────────────────────────────
    # 1. Create transactions — mix of valid and invalid
    # ──────────────────────────────────────────
    transactions: list[Transaction] = [
        # Valid credits (within limit)
        CreditTransaction(
            id="TXN001", amount=50000, currency="INR",
            status=TransactionStatus.PENDING, created_at="2025-01-15",
            credit_limit=100000,
        ),
        CreditTransaction(
            id="TXN002", amount=25000, currency="USD",
            status=TransactionStatus.PENDING, created_at="2025-01-15",
            credit_limit=50000,
        ),

        # Invalid credit — exceeds limit (should FAIL)
        CreditTransaction(
            id="TXN003", amount=150000, currency="INR",
            status=TransactionStatus.PENDING, created_at="2025-01-16",
            credit_limit=100000,
        ),

        # Valid debits (within balance)
        DebitTransaction(
            id="TXN004", amount=2000, currency="INR",
            status=TransactionStatus.PENDING, created_at="2025-01-16",
            account_balance=50000,
        ),
        DebitTransaction(
            id="TXN005", amount=8000, currency="EUR",
            status=TransactionStatus.PENDING, created_at="2025-01-17",
            account_balance=30000,
        ),

        # Invalid debit — exceeds balance (should FAIL)
        DebitTransaction(
            id="TXN006", amount=75000, currency="INR",
            status=TransactionStatus.PENDING, created_at="2025-01-17",
            account_balance=50000,
        ),

        # Invalid — negative amount (should FAIL)
        CreditTransaction(
            id="TXN007", amount=-500, currency="INR",
            status=TransactionStatus.PENDING, created_at="2025-01-18",
        ),

        # Valid ones
        DebitTransaction(
            id="TXN008", amount=1200, currency="USD",
            status=TransactionStatus.PENDING, created_at="2025-01-18",
            account_balance=5000,
        ),
        CreditTransaction(
            id="TXN009", amount=90000, currency="INR",
            status=TransactionStatus.PENDING, created_at="2025-01-19",
            credit_limit=100000,
        ),
        DebitTransaction(
            id="TXN010", amount=300, currency="EUR",
            status=TransactionStatus.PENDING, created_at="2025-01-19",
            account_balance=10000,
        ),
    ]

    # ──────────────────────────────────────────
    # 2. Create processor and add transactions
    # ──────────────────────────────────────────
    processor = TransactionProcessor()
    processor.add_many(transactions)

    print(f"Loaded {len(processor.transactions)} transactions")

    # ──────────────────────────────────────────
    # 3. Process all
    # ──────────────────────────────────────────
    results = processor.process_all()

    # ──────────────────────────────────────────
    # 4. Print each result
    # ──────────────────────────────────────────
    print()
    print("PROCESSING RESULTS:")
    print("-" * 50)
    for result in results:
        print(f"  {result}")

    # ──────────────────────────────────────────
    # 5. Print summary
    # ──────────────────────────────────────────
    processor.print_summary()

    # ──────────────────────────────────────────
    # 6. Query processed data
    # ──────────────────────────────────────────
    completed = processor.get_completed()
    failed = processor.get_failed()

    print()
    print(f"Completed transaction IDs: {[t.id for t in completed]}")
    print(f"Failed transaction IDs:    {[t.id for t in failed]}")

    # Verify statuses actually changed
    print()
    print("STATUS CHECK:")
    for txn in transactions:
        print(f"  {txn.id}: {txn.status.value}")

    # ──────────────────────────────────────────
    # 7. Analytics — Day 4
    # ──────────────────────────────────────────
    analytics = TransactionAnalytics(transactions)

    # Full report
    analytics.print_report()

    # Play with individual methods
    print("\n--- Individual method demos ---\n")

    # Group by status
    groups = analytics.group_by_status()
    for status, txns in groups.items():
        print(f"{status.value}: {[t.id for t in txns]}")

    # Unique currencies
    print(f"\nCurrencies used: {analytics.unique_currencies()}")

    # Build index — O(1) lookup
    index = analytics.build_index()
    print(f"\nLookup TXN003: {index['TXN003']}")

    # Filter with lambda
    high_value = analytics.filter_by(lambda t: t.amount > 10000)
    print(f"\nHigh value (>10K): {[t.id for t in high_value]}")

    inr_completed = analytics.filter_by(
        lambda t: t.currency == "INR" and t.status == TransactionStatus.COMPLETED
    )
    print(f"INR + Completed: {[t.id for t in inr_completed]}")

if __name__ == "__main__":
    main()