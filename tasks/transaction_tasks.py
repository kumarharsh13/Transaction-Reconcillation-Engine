import time
from tasks.celery_app import celery_app
from database.connection import SessionLocal
from database.repository import TransactionRepository

repo = TransactionRepository()


@celery_app.task(name="process_transaction")
def process_transaction(txn_id: str) -> dict:
  db = SessionLocal()

  try:
    # Fetch transaction from database
    txn = repo.get_by_id(db, txn_id)
    if not txn:
      return {"id": txn_id, "status": "ERROR", "reason": "Not found"}

    if txn.status in ("COMPLETED", "FAILED"):
      return {"id": txn_id, "status": "SKIPPED", "reason": f"Already {txn.status}"}

    # Simulate slow external API call
    # In real life: call payment gateway, fraud check, etc.
    time.sleep(1)

    # Validate based on type
    if txn.type == "CREDIT":
      limit = txn.credit_limit or 100000
      if txn.amount > limit:
        txn.status = "FAILED"
        db.commit()
        return {"id": txn_id, "status": "FAILED", "reason": "Credit limit exceeded"}

    elif txn.type == "DEBIT":
      balance = txn.account_balance or 50000
      if txn.amount > balance:
        txn.status = "FAILED"
        db.commit()
        return {"id": txn_id, "status": "FAILED", "reason": "Insufficient balance"}


    txn.status = "COMPLETED"
    db.commit()
    return {"id": txn_id, "status": "COMPLETED"}

  except Exception as e:
      db.rollback()
      return {"id": txn_id, "status": "ERROR", "reason": str(e)}

  finally:
      db.close()


@celery_app.task(name="process_batch")
def process_batch(txn_ids: list[str]) -> dict:
    results = []
    completed = 0
    failed = 0

    db = SessionLocal()

    try:
      for txn_id in txn_ids:
        txn = repo.get_by_id(db, txn_id)
        if not txn or txn.status in ("COMPLETED", "FAILED"):
          continue

        # Simulate API call
        time.sleep(0.5)

        # Validate
        new_status = "COMPLETED"

        if txn.type == "CREDIT":
          limit = txn.credit_limit or 100000
          if txn.amount > limit:
              new_status = "FAILED"

        elif txn.type == "DEBIT":
          balance = txn.account_balance or 50000
          if txn.amount > balance:
              new_status = "FAILED"

        txn.status = new_status
        db.commit()

        if new_status == "COMPLETED":
          completed += 1
        else:
          failed += 1

        results.append({"id": txn_id, "status": new_status})

      return {
          "total": len(txn_ids),
          "completed": completed,
          "failed": failed,
          "results": results,
      }

    except Exception as e:
        db.rollback()
        return {"error": str(e)}

    finally:
        db.close()


@celery_app.task(name="generate_report")
def generate_report() -> dict:
    db = SessionLocal()

    try:
      all_txns = repo.get_all(db)
      status_counts = repo.count_by_status(db)
      amount_by_status = repo.total_amount_by_status(db)

      # Simulate heavy computation
      time.sleep(2)

      return {
          "total_transactions": len(all_txns),
          "by_status": status_counts,
          "amount_by_status": amount_by_status,
          "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
      }

    finally:
      db.close()