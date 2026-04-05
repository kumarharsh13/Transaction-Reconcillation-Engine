import uuid

from tasks.transaction_tasks import process_transaction as process_transaction_task, process_batch, generate_report
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database.connection import get_db
from database.repository import TransactionRepository
from database.models import TransactionDB
from models.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionType,
    TransactionStatusEnum,
    ProcessingSummary,
)

# ── App ───────────────────────────────────────────
app = FastAPI(title="Transaction API (PostgreSQL)")

# ── Repository instance ──────────────────────────
# One instance, reused across all endpoints
repo = TransactionRepository()


# ── Helper ────────────────────────────────────────
def generate_id() -> str:
  return f"TXN-{uuid.uuid4().hex[:8].upper()}"


# ── POST /transactions/ ──────────────────────────
@app.post("/transactions/", response_model = TransactionResponse)
def create_transaction(txn: TransactionCreate,db: Session = Depends(get_db)):
  txn_data = {
    "id": generate_id(),
    "type": txn.type.value,
    "amount": txn.amount,
    "currency": txn.currency,
    "status": "PENDING",
    "credit_limit": txn.credit_limit,
    "account_balance": txn.account_balance,
  }

  db_txn = repo.create(db, txn_data)
  return _to_response(db_txn)


# ── GET /transactions/ ───────────────────────────
@app.get("/transactions/", response_model=list[TransactionResponse])
def list_transactions(status: Optional[str] = None, currency: Optional[str] = None, min_amount: Optional[float] = None, db: Session = Depends(get_db)):
  txns = repo.get_filtered(db, status=status, currency=currency, min_amount=min_amount)
  return [_to_response(t) for t in txns]


# ── GET /transactions/{txn_id} ───────────────────
@app.get("/transactions/{txn_id}", response_model=TransactionResponse)
def get_transaction(txn_id: str,db: Session = Depends(get_db)):
  txn = repo.get_by_id(db, txn_id)
  if not txn:
    raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found")
  return _to_response(txn)


# ── PUT /transactions/{txn_id} ───────────────────
@app.put("/transactions/{txn_id}", response_model=TransactionResponse)
def update_transaction(txn_id: str,update: TransactionUpdate,db: Session = Depends(get_db)):
  # Build update dict, excluding None values
  update_data = {}
  if update.status is not None:
      update_data["status"] = update.status.value
  if update.amount is not None:
      update_data["amount"] = update.amount
  if update.currency is not None:
      update_data["currency"] = update.currency

  if not update_data:
    raise HTTPException(status_code=400, detail="No fields to update")

  txn = repo.update(db, txn_id, update_data)
  if not txn:
    raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found")

  return _to_response(txn)


# ── DELETE /transactions/{txn_id} ────────────────
@app.delete("/transactions/{txn_id}")
def delete_transaction(txn_id: str, db: Session = Depends(get_db),):
  deleted = repo.delete(db, txn_id)
  if not deleted:
    raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found")

  return {"message": f"Transaction {txn_id} deleted"}


# ── POST /transactions/{txn_id}/process ──────────
@app.post("/transactions/{txn_id}/process", response_model=TransactionResponse)
def process_transaction(txn_id: str,db: Session = Depends(get_db)):
  txn = repo.get_by_id(db, txn_id)
  if not txn:
    raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found")

  if txn.status != "PENDING":
    raise HTTPException(status_code=400, detail=f"Transaction already {txn.status}")

  new_status = "COMPLETED"

  if txn.type == "CREDIT":
    limit = txn.credit_limit or 100000
    if txn.amount > limit:
      new_status = "FAILED"

  elif txn.type == "DEBIT":
    balance = txn.account_balance or 50000
    if txn.amount > balance:
      new_status = "FAILED"

  txn = repo.update_status(db, txn_id, new_status)
  return _to_response(txn)


# ── GET /analytics/summary ───────────────────────
@app.get("/analytics/summary", response_model=ProcessingSummary)
def get_summary(db: Session = Depends(get_db)):
  status_counts = repo.count_by_status(db)
  total = sum(status_counts.values())

  if total == 0:
    return ProcessingSummary(
      total=0, completed=0, failed=0,
      success_rate=0, total_amount=0, by_currency={},
    )

  completed_count = status_counts.get("COMPLETED", 0)
  failed_count = status_counts.get("FAILED", 0)

  amount_by_status = repo.total_amount_by_status(db)
  total_amount = amount_by_status.get("COMPLETED", 0)

  currency_counts = repo.count_by_currency(db)

  return ProcessingSummary(
    total=total,
    completed=completed_count,
    failed=failed_count,
    success_rate=round(completed_count / total * 100, 1) if total > 0 else 0,
    total_amount=total_amount,
    by_currency=currency_counts,
  )


# ── GET /health ──────────────────────────────────
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
  """Health check — also verifies database connection"""
  try:
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}
  except Exception as e:
    raise HTTPException(status_code=503, detail={"status": "unhealthy", "database": str(e)})


# ── Helper: Convert DB model to response dict ────
def _to_response(txn: TransactionDB) -> dict:
  """
  Convert a SQLAlchemy model to a dict that matches TransactionResponse.

  Why? SQLAlchemy models have database-specific stuff
  that Pydantic doesn't understand directly.
  This helper bridges the gap.
  """
  return {
    "id": txn.id,
    "amount": txn.amount,
    "currency": txn.currency,
    "type": txn.type,
    "status": txn.status,
    "created_at": txn.created_at.isoformat() if txn.created_at else "",
  }

# ── POST /jobs/process/{txn_id} — Background process ─
@app.post("/jobs/process/{txn_id}")
def enqueue_process(txn_id: str, db: Session = Depends(get_db)):
  txn = repo.get_by_id(db, txn_id)
  if not txn:
    raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found")

  if txn.status != "PENDING":
    raise HTTPException(status_code=400, detail=f"Transaction already {txn.status}")

  task = process_transaction_task.delay(txn_id)

  return {
    "task_id": task.id,
    "status": "queued",
    "message": f"Transaction {txn_id} queued for processing",
  }


# ── POST /jobs/process-batch — Background batch process ─
@app.post("/jobs/process-batch")
def enqueue_batch_process(db: Session = Depends(get_db)):
  pending_txns = repo.get_by_status(db, "PENDING")

  if not pending_txns:
    return {"message": "No pending transactions to process"}

  txn_ids = [txn.id for txn in pending_txns]

  task = process_batch.delay(txn_ids)

  return {
    "task_id": task.id,
    "status": "queued",
    "pending_count": len(txn_ids),
    "message": f"{len(txn_ids)} transactions queued for processing",
  }


# ── POST /jobs/report — Background report generation ─
@app.post("/jobs/report")
def enqueue_report():
    task = generate_report.delay()

    return {
      "task_id": task.id,
      "status": "queued",
      "message": "Report generation started",
    }


# ── GET /jobs/{task_id} — Check task status ──────
@app.get("/jobs/{task_id}")
def get_task_status(task_id: str):
  from tasks.celery_app import celery_app

  # AsyncResult fetches task info from Redis
  result = celery_app.AsyncResult(task_id)


  response = {
      "task_id": task_id,
      "status": result.status,
  }

  # If task is done, include the result
  if result.ready():
      response["result"] = result.result

  # If task failed, include the error
  if result.failed():
      response["error"] = str(result.result)

  return response