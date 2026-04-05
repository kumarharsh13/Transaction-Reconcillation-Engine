from models.transaction import (
  Transaction,
  TransactionStatus
)

from models.result import TransactionResult

from models.exceptions import (
  InvalidTransactionException,
  InsufficientBalanceException,
  CreditLimitExceededException,
)

class TransactionProcessor:

  def __init__(self) -> None:
    self.transactions: list[Transaction] = []
    self.results: list[TransactionResult] = []

  def add(self, transaction: Transaction) -> None:
    self.transactions.append(transaction)

  def add_many(self, transactions: list[Transaction]) -> None:
    self.transactions.extend(transactions)

  def process_all(self) -> list[TransactionResult]:
    self.results = []

    for txn in self.transactions:
      result = self._process_single(txn)
      self.results.append(result)

    return self.results
    
  def _process_single(self, txn: Transaction) -> TransactionResult:
    try:
      txn.validate()
      txn.status = TransactionStatus.COMPLETED

      return TransactionResult(txn, success=True)
    except CreditLimitExceededException as e:
      txn.status = TransactionStatus.FAILED
      return TransactionResult(txn, success=False, error_message=str(e))

    except InsufficientBalanceException as e:
      txn.status = TransactionStatus.FAILED
      return TransactionResult(txn, success=False, error_message=str(e))

    except InvalidTransactionException as e:
      txn.status = TransactionStatus.FAILED
      return TransactionResult(txn, success=False, error_message=str(e))

    except Exception as e:
      txn.status = TransactionStatus.FAILED
      return TransactionResult(
          txn, success=False, error_message=f"Unexpected: {e}"
      )

  def get_completed(self) -> list[Transaction]:
    return [r.transaction for r in self.results if r.success]
  
  def get_failed(self) -> list[Transaction]:
    return [r.transaction for r in self.results if not r.success]

  def get_by_status(self, status: TransactionStatus) -> list[Transaction]:
    return [t for t in self.transactions if t.status == status]

  def get_total_amount(self) -> float:
    return sum(t.amount for t in self.get_completed())

  def print_summary(self) -> None:
    total = len(self.results)
    completed = len(self.get_completed())
    failed = len(self.get_failed())
    total_amount = self.get_total_amount()

    print()
    print("=" * 50)
    print("  PROCESSING SUMMARY")
    print("=" * 50)
    print(f"  Total processed:  {total}")
    print(f"  Completed:        {completed}")
    print(f"  Failed:           {failed}")
    print(f"  Success rate:     {completed/total*100:.1f}%" if total > 0 else "  Success rate:     N/A")
    print(f"  Total amount:     ₹{total_amount:,.2f}")
    print("=" * 50)

    if failed > 0:
      print()
      print("  FAILED TRANSACTIONS:")
      print("-" * 50)
      for r in self.results:
        if not r.success:
          print(f"  {r}")