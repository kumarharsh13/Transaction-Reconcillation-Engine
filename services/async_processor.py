import asyncio
import time
from models.transaction import Transaction, TransactionStatus
from models.result import TransactionResult
from models.exceptions import InvalidTransactionException

class AsyncTransactionProcessor:
  def __init__(self) -> None:
    self.results: list[TransactionResult] = []

  async def process_single(self, txn: Transaction) -> TransactionResult:
    await asyncio.sleep(0.1)

    try:
      txn.validate()
      txn.status = TransactionStatus.COMPLETED
      return TransactionResult(txn, success = True)
    except InvalidTransactionException as e:
      txn.status = TransactionStatus.FAILED
      return TransactionResult(txn, success=False, error_message=str(e))
    except Exception as e:
      txn.status = TransactionStatus.FAILED
      return TransactionResult(txn, success=False, error_message=f"Unexpected: {e}")

  async def process_all_concurrent(self, transactions: list[Transaction]) -> list[TransactionResult]:
    tasks = [self.process_single(txn) for txn in transactions]
    self.results = await asyncio.gather(*tasks)
    return self.results

  async def process_all_sequential(self, transactions: list[Transaction]) -> list[TransactionResult]:
    self.results = []
    for txn in transactions:
      result = await self.process_single(txn)
      self.results.append(result)
    return self.results
  
  def get_completed(self) -> list[Transaction]:
    return [r.transaction for r in self.results if r.success]

  def get_failed(self) -> list[Transaction]:
    return [r.transaction for r in self.results if not r.success]
  
async def demo():
  from models.transaction import CreditTransaction, DebitTransaction

  # Create 100 test transactions
  transactions: list[Transaction] = []
  for i in range(1, 101):
      if i % 2 == 0:
          txn = DebitTransaction(
              id=f"TXN{i:03d}",
              amount=1000 * i,
              currency="INR",
              status=TransactionStatus.PENDING,
              created_at="2025-01-15",
              account_balance=50000,
          )
      else:
          txn = CreditTransaction(
              id=f"TXN{i:03d}",
              amount=1000 * i,
              currency="INR",
              status=TransactionStatus.PENDING,
              created_at="2025-01-15",
              credit_limit=100000,
          )
      transactions.append(txn)

  processor = AsyncTransactionProcessor()

  # ── Sequential ──────────────────────────────────
  print("=" * 55)
  print("  SEQUENTIAL PROCESSING")
  print("=" * 55)

  # Reset statuses for fair comparison
  for t in transactions:
    t.status = TransactionStatus.PENDING

  start = time.time()
  results = await processor.process_all_sequential(transactions)
  sequential_time = time.time() - start

  completed = len(processor.get_completed())
  failed = len(processor.get_failed())
  print(f"  Transactions: {len(transactions)}")
  print(f"  Completed:    {completed}")
  print(f"  Failed:       {failed}")
  print(f"  Time:         {sequential_time:.2f}s")
  print()

  # ── Concurrent ──────────────────────────────────
  print("=" * 55)
  print("  CONCURRENT PROCESSING (async)")
  print("=" * 55)

  # Reset statuses
  for t in transactions:
      t.status = TransactionStatus.PENDING

  start = time.time()
  results = await processor.process_all_concurrent(transactions)
  concurrent_time = time.time() - start

  completed = len(processor.get_completed())
  failed = len(processor.get_failed())
  print(f"  Transactions: {len(transactions)}")
  print(f"  Completed:    {completed}")
  print(f"  Failed:       {failed}")
  print(f"  Time:         {concurrent_time:.2f}s")
  print()

  # ── Comparison ──────────────────────────────────
  speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0
  print("=" * 55)
  print("  COMPARISON")
  print("=" * 55)
  print(f"  Sequential: {sequential_time:.2f}s")
  print(f"  Concurrent: {concurrent_time:.2f}s")
  print(f"  Speedup:    {speedup:.1f}x faster")
  print("=" * 55)

  # ── Print individual results ────────────────────
  print()
  print("RESULTS:")
  for r in results:
      print(f"  {r}")


# This is how you run async code from a regular Python file
# asyncio.run() creates the event loop and runs your async function
if __name__ == "__main__":
  asyncio.run(demo())


# python3 -m services.async_processor to run this seperately 