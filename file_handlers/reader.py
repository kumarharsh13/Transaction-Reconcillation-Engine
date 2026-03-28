import csv
from models.transaction import (
  Transaction,
  TransactionStatus,
  CreditTransaction,
  DebitTransaction
)

class TransactionFileReader:
  def read_csv(self, file_path: str) -> tuple[list[Transaction], list[str]]:
    transactions: list[Transaction] = []
    errors: list[str] = []
    row_count = 0

    with open(file_path, mode = 'r') as file:
      reader = csv.DictReader(file)

      for row_count, row in enumerate(reader, start = 2):
        row_count += 1
        try:
          txn = self._parse_transaction(row)
          transactions.append(txn)
        except Exception as e:
          errors.append(f"Row {row_count}: {str(e)}")

    print(f"Read {row_count} rows: {len(transactions)} success, {len(errors)} errors")
    return transactions, errors
  
  def _parse_transaction(self, row: dict) -> Transaction:
    txn_id = row.get('id').strip()
    txn_type = row.get('type').strip().upper()
    currency = row.get('currency').strip().upper()
    date = row.get('date').strip()
    amount = float(row.get('amount').strip())

    if txn_type == "CREDIT":
      return CreditTransaction(
        id=txn_id,
        amount=amount,
        currency=currency,
        status=TransactionStatus.PENDING,
        created_at=date,
        credit_limit=100_000.0,
      )
    elif txn_type == "DEBIT":
      return DebitTransaction(
        id=txn_id,
        amount=amount,
        currency=currency,
        status=TransactionStatus.PENDING,
        created_at=date,
        account_balance=50_000.0,
      )
    else:
      raise ValueError(f"Unknown transaction type: '{txn_type}'")