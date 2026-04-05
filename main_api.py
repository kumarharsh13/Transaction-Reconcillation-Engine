import uuid
import csv
import io

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime
from models.schemas import (
  TransactionCreate,
  TransactionResponse,
  TransactionUpdate,
  TransactionType,
  TransactionStatusEnum,
  ProcessingSummary,
  BatchTransactionCreate,
  BatchResult,
  UploadResult,
)

app = FastAPI(
  title = "Transaction Reconciliation Engine API",
  description = "API for processing and reconciling financial transactions",
  version = "1.0.0"
)

transactions_db: dict[str, dict] = {}

def generate_id() -> str:
  return f"TXN-{uuid.uuid4().hex[:8].upper()}"

@app.post("/transactions/", response_model = TransactionResponse)
async def create_transaction(txn: TransactionCreate):
  txn_id = generate_id()
  now = datetime.now().isoformat()

  txn_data = {
    "id": txn_id,
    "amount": txn.amount,
    "currency": txn.currency,
    "type": txn.type.value,
    "status": TransactionStatusEnum.PENDING.value,
    "created_at": now,
    "credit_limit": txn.credit_limit,
    "account_balance": txn.account_balance,
  }
  
  transactions_db[txn_id] = txn_data
  
  return txn_data 

@app.get("/transactions/", response_model = list[TransactionResponse])
async def list_transactions(status: Optional[str] = None, currency: Optional[str] = None, min_amount: Optional[float] = None):
  result = list(transactions_db.values())

  if status:
    result = [t for t in result if t["status"] == status.upper()]
  if currency:
    result = [t for t in result if t["currency"] == currency.upper()]
  if min_amount:
    result = [t for t in result if t["amount"] >= min_amount]

  return result

@app.get("/transactions/{txn_id}", response_model = TransactionResponse)
async def get_transaction(txn_id: str):
  if txn_id not in transactions_db:
    raise HTTPException(status_code = 404, detail = f"Transaction {txn_id} not found")
  return transactions_db[txn_id]

@app.put("/transactions/{txn_id}", response_model = TransactionResponse)
async def update_transaction(txn_id: str, update: TransactionUpdate):
  if txn_id not in transactions_db:
    raise HTTPException(status_code = 404, detail = f"Transaction {txn_id} not found")
  
  txn_data = transactions_db[txn_id]
  update_data = update.model_dump(exclude_none = True)
  for key, value in update_data.items():
    if key == "status":
      txn_data[key] = value.value
    else:
      txn_data[key] = value

  return txn_data

@app.delete("/transactions/{txn_id}")
async def delete_transaction(txn_id: str):
    if txn_id not in transactions_db:
      raise HTTPException(status_code = 404, detail = f"Transaction {txn_id} not found")
    
    del transactions_db[txn_id]
    return {"message": f"Transaction {txn_id} deleted"}

@app.post("/transactions/{txn_id}/process", response_model = TransactionResponse)
async def process_transaction(txn_id: str):
  if txn_id not in transactions_db:
    raise HTTPException(status_code = 404, detail = f"Transaction {txn_id} not found")
  
  txn_data = transactions_db[txn_id]

  if txn_data["status"] != TransactionStatusEnum.PENDING.value:
    raise HTTPException(status_code = 400, detail = f"Transaction {txn_id} is already processed")
  
  if txn_data["type"] == TransactionType.CREDIT.value:
    limit = txn_data.get("credit_limit") or 100000
    if txn_data["amount"] > limit:
      txn_data["status"] = TransactionStatusEnum.FAILED.value
      return txn_data
  elif txn_data["type"] == TransactionType.DEBIT.value:
    balance = txn_data.get("account_balance") or 50000
    if txn_data["amount"] > balance:
      txn_data["status"] = TransactionStatusEnum.FAILED.value
      return txn_data

  txn_data["status"] = TransactionStatusEnum.COMPLETED.value
  return txn_data

@app.get("/analytics/summary", response_model=ProcessingSummary)
async def get_summary():
  all_txns = list(transactions_db.values())
  total = len(all_txns)

  if total == 0:
    return ProcessingSummary(
      total=0, completed=0, failed=0,
      success_rate=0, total_amount=0, by_currency={},
    )

  completed = [t for t in all_txns if t["status"] == "COMPLETED"]
  failed = [t for t in all_txns if t["status"] == "FAILED"]

  from collections import Counter
  currency_counts = Counter(t["currency"] for t in all_txns)

  return ProcessingSummary(
    total=total,
    completed=len(completed),
    failed=len(failed),
    success_rate=round(len(completed) / total * 100, 1) if total > 0 else 0,
    total_amount=sum(t["amount"] for t in completed),
    by_currency=dict(currency_counts),
  )

@app.get("/health")
async def health_check():
  return {
    "status": "healthy",
    "transactions_count": len(transactions_db),
  }

@app.post("/upload/csv", response_model = UploadResult)
async def upload_csv(file: UploadFile = File(...)):
  content = await file.read()
  text = content.decode("utf-8")

  csv_reader = csv.DictReader(io.StringIO(text))
  created, row_count, errors = 0, 0, []
  for row_num, row in enumerate(csv_reader, start = 2):
    row_count += 1
    try:
      txn_type = row.get("type", "").strip().upper()
      amount = float(row.get("amount", 0))
      currency = row.get("currency", "").strip().upper()

      txn_id = generate_id()
      now = datetime.now().isoformat()

      txn_data = {
        "id": txn_id,
        "amount": amount,
        "currency": currency,
        "type": txn_type,
        "status": TransactionStatusEnum.PENDING.value,
        "created_at": now,
        "credit_limit": float(row.get("credit_limit", 0) or 100000),
        "account_balance": float(row.get("account_balance", 0) or 50000),
      }
      transactions_db[txn_id] = txn_data
      created += 1

    except Exception as e:
      errors.append(f"Row {row_num}: {str(e)}")

  return UploadResult(
    total_rows=row_count,
    parsed=created,
    parse_errors=len(errors),
    created=created,
    errors=errors
  )

@app.post("/transactions/batch", response_model = BatchResult)
async def create_batch(batch: BatchTransactionCreate):
  results, successful, failed = [], 0, 0

  for txn in batch.transactions:
    try:
      txn_id = generate_id()
      now = datetime.now().isoformat()

      txn_data = {
        "id": txn_id,
        "amount": txn.amount,
        "currency": txn.currency,
        "type": txn.type.value,
        "status": TransactionStatusEnum.PENDING.value,
        "created_at": now,
        "credit_limit": txn.credit_limit,
        "account_balance": txn.account_balance,
      }
      transactions_db[txn_id] = txn_data
      results.append({"id": txn_id, "status": "created"})
      successful += 1

    except Exception as e:
      results.append({"error": str(e)})
      failed += 1

  return BatchResult(
    total=len(batch.transactions),
    successful=successful,
    failed=failed,
    results=results,
  )

@app.post("/transactions/process_all", response_model = BatchResult)
async def process_all_pending():
  results, successful, failed = [], 0, 0
  pending = {
    txn_id: txn_data
    for txn_id, txn_data in transactions_db.items()
    if txn_data["status"] == TransactionStatusEnum.PENDING.value
  }

  for txn_id, txn_data in pending.items():
    try:
      if txn_data["type"] == TransactionType.CREDIT.value:
        limit = txn_data.get("credit_limit") or 100000
        if txn_data["amount"] > limit:
          txn_data["status"] = TransactionStatusEnum.FAILED.value
          results.append({"id": txn_id, "status": "FAILED", "reason": "Credit limit exceeded"})
          failed += 1
          continue

      elif txn_data["type"] == TransactionType.DEBIT.value:
        balance = txn_data.get("account_balance") or 50000
        if txn_data["amount"] > balance:
          txn_data["status"] = TransactionStatusEnum.FAILED.value
          results.append({"id": txn_id, "status": "FAILED", "reason": "Insufficient balance"})
          failed += 1
          continue

      txn_data["status"] = TransactionStatusEnum.COMPLETED.value
      results.append({"id": txn_id, "status": "COMPLETED"})
      successful += 1

    except Exception as e:
      txn_data["status"] = TransactionStatusEnum.FAILED.value
      results.append({"id": txn_id, "status": "FAILED", "reason": str(e)})
      failed += 1

  return BatchResult(
    total=len(pending),
    successful=successful,
    failed=failed,
    results=results,
  )
  
@app.get("/export/csv")
async def export_csv(status: Optional[str] = None):
  txns = list(transactions_db.values())
  if status:
    txns  = [t for t in txns if t["status"] == status.upper()]

  output = io.StringIO()
  fieldnames = ["id", "type", "amount", "currency", "status", "created_at"]
  writer = csv.DictWriter(output, fieldnames=fieldnames)
  writer.writeheader()

  for txn in txns:
    writer.writerow({
      "id": txn["id"],
      "type": txn["type"],
      "amount": txn["amount"],
      "currency": txn["currency"],
      "status": txn["status"],
      "created_at": txn["created_at"],
    })

  output.seek(0)

  return StreamingResponse(
    output,
    media_type="text/csv",
    headers={"Content-Disposition": "attachment; filename=transactions.csv"},
  )