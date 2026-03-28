import os
from models.transaction import TransactionStatus
from services.processor import TransactionProcessor
from services.analytics import TransactionAnalytics
from file_handlers.reader import TransactionFileReader
from file_handlers.writer import TransactionFileWriter


def main():
    input_file = "data/transactions.csv"
    output_dir = "data/output"

    os.makedirs(output_dir, exist_ok=True)

    reader = TransactionFileReader()
    writer = TransactionFileWriter()
    processor = TransactionProcessor()

    # ──────────────────────────────────────────
    # Step 1: Read from CSV
    # ──────────────────────────────────────────
    print("STEP 1: Reading transactions from CSV...")
    print("-" * 50)

    transactions, parse_errors = reader.read_csv(input_file)
    # This returns TWO values — tuple unpacking
    # Ruby equivalent: transactions, parse_errors = reader.read_csv(input_file)

    if parse_errors:
        print(f"\nParse errors found:")
        for error in parse_errors:
            print(f"  {error}")

    # ──────────────────────────────────────────
    # Step 2: Process all transactions
    # ──────────────────────────────────────────
    print()
    print("STEP 2: Processing transactions...")
    print("-" * 50)

    processor.add_many(transactions)
    results = processor.process_all()

    for result in results:
        print(f"  {result}")

    processor.print_summary()

    # ──────────────────────────────────────────
    # Step 3: Run analytics
    # ──────────────────────────────────────────
    print()
    print("STEP 3: Running analytics...")
    print("-" * 50)

    analytics = TransactionAnalytics(transactions)
    analytics.print_report()

    # ──────────────────────────────────────────
    # Step 4: Write results to files
    # ──────────────────────────────────────────
    print()
    print("STEP 4: Writing output files...")
    print("-" * 50)

    completed = processor.get_completed()
    failed = processor.get_failed()

    writer.write_transactions_csv(
        completed,
        os.path.join(output_dir, "completed.csv"),
    )

    writer.write_transactions_csv(
        failed,
        os.path.join(output_dir, "failed.csv"),
    )

    writer.write_errors(
        parse_errors,
        os.path.join(output_dir, "parse_errors.txt"),
    )

    # ──────────────────────────────────────────
    # Step 5: Final summary
    # ──────────────────────────────────────────
    print()
    print("=" * 50)
    print("  PIPELINE COMPLETE")
    print("=" * 50)
    print(f"  Input:          {input_file}")
    print(f"  Total rows:     {len(transactions) + len(parse_errors)}")
    print(f"  Parsed OK:      {len(transactions)}")
    print(f"  Parse errors:   {len(parse_errors)}")
    print(f"  Completed:      {len(completed)}")
    print(f"  Failed:         {len(failed)}")
    print(f"  Output dir:     {output_dir}/")
    print("=" * 50)


if __name__ == "__main__":
    main()