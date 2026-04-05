from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from database.models import TransactionDB


class TransactionRepository:
  # ── CREATE ────────────────────────────────────

  def create(self, db: Session, txn_data: dict) -> TransactionDB:
    txn = TransactionDB(**txn_data)
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn

  # ── READ ──────────────────────────────────────

  def get_by_id(self, db: Session, txn_id: str) -> Optional[TransactionDB]:
    return db.get(TransactionDB, txn_id)

  def get_all(self, db: Session) -> list[TransactionDB]:
    return db.query(TransactionDB).all()

  def get_by_status(self, db: Session, status: str) -> list[TransactionDB]:
    return (
      db.query(TransactionDB)
      .filter(TransactionDB.status == status)
      .all()
    )

  def get_by_currency(self, db: Session, currency: str) -> list[TransactionDB]:
    return (
      db.query(TransactionDB)
      .filter(TransactionDB.currency == currency)
      .all()
    )

  def get_filtered( self, db: Session, status: Optional[str] = None, currency: Optional[str] = None, min_amount: Optional[float] = None) -> list[TransactionDB]:
    query = db.query(TransactionDB)

    if status:
      query = query.filter(TransactionDB.status == status.upper())
    if currency:
      query = query.filter(TransactionDB.currency == currency.upper())
    if min_amount:
      query = query.filter(TransactionDB.amount >= min_amount)

    return query.all()

  # ── UPDATE ────────────────────────────────────

  def update_status(self, db: Session, txn_id: str, new_status: str) -> Optional[TransactionDB]:
    txn = self.get_by_id(db, txn_id)
    if not txn:
      return None

    txn.status = new_status
    db.commit()
    db.refresh(txn)
    return txn

  def update(self, db: Session, txn_id: str, update_data: dict) -> Optional[TransactionDB]:
    txn = self.get_by_id(db, txn_id)
    if not txn:
      return None

    for key, value in update_data.items():
      setattr(txn, key, value)

    db.commit()
    db.refresh(txn)
    return txn

  # ── DELETE ────────────────────────────────────

  def delete(self, db: Session, txn_id: str) -> bool:
    txn = self.get_by_id(db, txn_id)
    if not txn:
      return False

    db.delete(txn)
    db.commit()
    return True

  # ── AGGREGATE ─────────────────────────────────

  def count_by_status(self, db: Session) -> dict[str, int]:

    results = (
      db.query(TransactionDB.status, func.count(TransactionDB.id))
      .group_by(TransactionDB.status)
      .all()
    )
    
    return {status: count for status, count in results}

  def count_by_currency(self, db: Session) -> dict[str, int]:
    results = (
      db.query(TransactionDB.currency, func.count(TransactionDB.id))
      .group_by(TransactionDB.currency)
      .all()
    )
    return {currency: count for currency, count in results}

  def total_amount_by_status(self, db: Session) -> dict[str, float]:

    results = (
      db.query(TransactionDB.status, func.sum(TransactionDB.amount))
      .group_by(TransactionDB.status)
      .all()
    )
    return {status: float(total or 0) for status, total in results}