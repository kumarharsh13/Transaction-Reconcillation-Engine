import csv
from xml.parsers.expat import errors
from models.transaction import (
  Transaction,
  TransactionStatus,
  CreditTransaction,
  DebitTransaction
)

class TransactionFileWriter:
  def write_transactions_csv(self, transactions: list[Transaction], file_path: str) -> None:

    if not transactions:
      print(f"No transactions to write to {file_path}")
      return
    
    fieldnames = ["id", "type", "amount", "currency", "status", "date"]
    with open(file_path, mode = 'w', newline = '') as file:
      writer = csv.DictWriter(file, fieldnames = fieldnames)
      writer.writeheader()

      for txn in transactions:
        txn_type = "CREDIT" if isinstance(txn, CreditTransaction) else "DEBIT"

        writer.writerow({
          "id": txn.id,
          "type": txn_type,
          "amount": f"{txn.amount:.2f}",
          "currency": txn.currency,
          "status": txn.status.value,
          "date": txn.created_at
        })

      print(f"Wrote {len(transactions)} transactions to {file_path}")

  def write_errors(self, errors: list[str], file_path: str) -> None:
    if not errors:
      print(f"No errors to write to {file_path}")
      return
    
    with open(file_path, "w") as f:
      for error in errors:
        f.write(error + "\n")

    print(f"Wrote {len(errors)} errors to {file_path}")
