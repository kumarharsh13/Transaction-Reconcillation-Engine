import os
from models.transaction import Transaction, TransactionStatus
from models.result import TransactionResult
from services.processor import TransactionProcessor
from services.analytics import TransactionAnalytics
from file_handlers.reader import TransactionFileReader
from file_handlers.writer import TransactionFileWriter

class ReconciliationEngine:
  def __init__(self) -> None:
    self.reader = TransactionFileReader()
    self.writer = TransactionFileWriter()
    self.processor = TransactionProcessor()
    self.analytics = None

    self.transactions: list[Transaction] = []
    self.parse_errors: list[str] = []
    self.results: list[TransactionResult] = []

  def run(self, input_file: str, output_dir: str) -> None:
    print("=" * 55)
    print("  RECONCILIATION ENGINE")
    print("=" * 55)
    print()
    print("[1/5] Reading transactions...")
    self.transactions, self.parse_errors = self.reader.read_csv(input_file)

    print()
    print("[2/5] Processing transactions...")
    self.processor.add_many(self.transactions)
    self.results = self.processor.process_all()

    completed = self.processor.get_completed()
    failed = self.processor.get_failed()

    print(f"      Completed: {len(completed)}")
    print(f"      Failed:    {len(failed)}")

    print()
    print("[3/5] Running analytics...")

    self.analytics = TransactionAnalytics(self.transactions)

    print()
    print("[4/5] Writing output files...")

    self.writer.write_transactions_csv(completed, os.path.join(output_dir, 'completed.csv'))
    self.writer.write_transactions_csv(failed, os.path.join(output_dir, 'failed.csv'))
    self.writer.write_errors(self.parse_errors, os.path.join(output_dir, 'parse_errors.txt'))

    print()
    print("[5/5] Generating report...")

    self._print_final_report(input_file, output_dir, completed, failed)

  def run_lazy(self, input_file: str) -> None:
    print("=" * 55)
    print("  LAZY PROCESSING (generator mode)")
    print("=" * 55)

    completed_count = 0
    failed_count = 0
    error_count = 0
    total_amount = 0.0

    for txn, error in self.reader.read_csv_lazy(input_file):
      if error:
        error_count += 1
        print(f"  SKIP: {error}")
        continue

      try:
        txn.validate()
        txn.status = TransactionStatus.COMPLETED
        completed_count += 1
        total_amount += txn.amount
      except Exception as e:
        txn.status = TransactionStatus.FAILED
        failed_count += 1

    total = completed_count + failed_count
    print()
    print(f"  Processed:  {total} transactions")
    print(f"  Completed:  {completed_count}")
    print(f"  Failed:     {failed_count}")
    print(f"  Total amt:  ₹{total_amount:,.2f}")
    print()
    print("  (Memory usage: minimal — one row at a time)")
    print("=" * 55)


  def _print_final_report(self,input_file: str,output_dir: str,completed: list[Transaction],failed: list[Transaction]) -> None:
    total_rows = len(self.transactions) + len(self.parse_errors)
    total_amount = sum(t.amount for t in completed)
    avg_amount = total_amount / len(completed) if completed else 0

    currency_counts = self.analytics.count_by_currency()
    top_currency = currency_counts.most_common(1)
    top_currency_str = (
        f"{top_currency[0][0]} ({top_currency[0][1]} txns)"
        if top_currency
        else "N/A"
    )

    if completed:
      highest = max(completed, key=lambda t: t.amount)
      highest_str = f"₹{highest.amount:,.2f} ({highest.id})"
    else:
      highest_str = "N/A"

    print()
    print("╔═══════════════════════════════════════════╗")
    print("║       RECONCILIATION REPORT               ║")
    print("╠═══════════════════════════════════════════╣")
    print(f"║  Input:          {input_file:<25}║")
    print(f"║  Total rows:     {total_rows:<25}║")
    print(f"║  Parse errors:   {len(self.parse_errors):<25}║")
    print(f"║  Validated:      {len(self.transactions):<25}║")
    print(f"║  Completed:      {len(completed):<25}║")
    print(f"║  Failed:         {len(failed):<25}║")
    print(f"║                                           ║")
    print(f"║  Total amount:   ₹{total_amount:<22,.2f}║")
    print(f"║  Avg amount:     ₹{avg_amount:<22,.2f}║")
    print(f"║  Top currency:   {top_currency_str:<25}║")
    print(f"║  Highest:        {highest_str:<25}║")
    print(f"║                                           ║")
    print(f"║  Output:         {output_dir + '/':<25}║")
    print("╚═══════════════════════════════════════════╝")
