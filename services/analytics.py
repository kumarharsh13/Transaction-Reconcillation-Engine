from collections import defaultdict, Counter

from models.transaction import (
  Transaction,
  CreditTransaction,
  DebitTransaction,
  TransactionStatus
)

class TransactionAnalytics:
  def __init__(self, transactions: list[Transaction]) -> None:
    self.transactions = transactions

  def group_by_status(self) -> dict[TransactionStatus, list[Transaction]]:
    groups: dict[TransactionStatus, list[Transaction]] = defaultdict(list)
    for txn in self.transactions:
      groups[txn.status].append(txn)
    return dict(groups)
    
  def group_by_currency(self) -> dict[str, list[Transaction]]:
    groups: dict[str, list[Transaction]] = defaultdict(list)
    for txn in self.transactions:
      groups[txn.currency].append(txn)
    return dict(groups)
    
  def count_by_status(self) -> Counter:
    return Counter(txn.status for txn in self.transactions)
  
  def count_by_currency(self) -> Counter:
    return Counter(txn.currency for txn in self.transactions)
  
  def count_by_type(self) -> dict[str, int]:
    credits = sum(1 for txn in self.transactions if isinstance(txn, CreditTransaction))
    debits = sum(1 for txn in self.transactions if isinstance(txn, DebitTransaction))
    return {"CREDIT": credits, "DEBIT": debits}
  
  def total_amount(self) -> float:
    return sum(txn.amount for txn in self.transactions)
  
  def total_amount_by_status(self) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)

    for txn in self.transactions:
      totals[txn.status.value] += txn.amount
    return dict(totals)
  
  def total_amount_by_currency(self) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for t in self.transactions:
      totals[t.currency] += t.amount
    return dict(totals)

  def average_amount(self) -> float:
    if not self.transactions:
      return 0.0
    return self.total_amount() / len(self.transactions)
  
  def unique_currencies(self) -> set[str]:
    return set(txn.currency for txn in self.transactions)
  
  def unique_status(self) -> set[TransactionStatus]:
    return set(txn.status for txn in self.transactions)
  
  def build_index(self) -> dict[str, Transaction]:
    return {txn.id: txn for txn in self.transactions}
  
  def sort_by_amount(self, descending: bool = False) -> list[Transaction]:
    return sorted(self.transactions, key=lambda t: t.amount, reverse=descending)
  
  def top_n_by_amount(self, n: int) ->list[Transaction]:
    return self.sort_by_amount(descending=True)[:n]
  
  def filter_by(self, predicate) -> list[Transaction]:
    return [txn for txn in self.transactions if predicate(txn)]
  
  def print_report(self) -> None:
    """Print a full analytics report"""
    print()
    print("=" * 55)
    print("  ANALYTICS REPORT")
    print("=" * 55)

    # Counts
    print()
    print(f"  Total transactions:  {len(self.transactions)}")
    for status, count in self.count_by_status().most_common():
      print(f"    {status}: {count}")

    # By currency
    print()
    print("  By currency:")
    for currency, count in self.count_by_currency().most_common():
      total = self.total_amount_by_currency()[currency]
      print(f"    {currency}: {count} txns, ₹{total:,.2f}")

    # By type
    print()
    type_counts = self.count_by_type()
    print(f"  Credits: {type_counts['CREDIT']}")
    print(f"  Debits:  {type_counts['DEBIT']}")

    # Amounts
    print()
    print(f"  Total amount:   ₹{self.total_amount():,.2f}")
    print(f"  Average amount: ₹{self.average_amount():,.2f}")

    # Top 3
    print()
    print("  Top 3 by amount:")
    for t in self.top_n_by_amount(3):
      print(f"    {t}")

    print()
    print("=" * 55)