from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.sql import func
from database.connection import Base


class TransactionDB(Base):
  __tablename__ = "transactions"


  id = Column(
    String,
    primary_key=True,
    doc="Unique transaction ID (e.g., TXN-A1B2C3D4)",
  )

  type = Column(
    String(10),
    nullable=False,
    doc="CREDIT or DEBIT",
  )

  amount = Column(
    Float,
    nullable=False,
    doc="Transaction amount",
  )

  currency = Column(
    String(3),
    nullable=False,
    doc="3-letter currency code",
  )

  status = Column(
    String(20),
    nullable=False,
    default="PENDING",
    doc="PENDING, COMPLETED, FAILED, REVERSED",
  )

  credit_limit = Column(
    Float,
    nullable=True,
    doc="Credit limit (only for CREDIT type)",
  )

  account_balance = Column(
    Float,
    nullable=True,
    doc="Account balance (only for DEBIT type)",
  )

  created_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    doc="When the transaction was created",
  )

  def __repr__(self):
    return (
      f"TransactionDB(id='{self.id}', type='{self.type}', "
      f"amount={self.amount}, status='{self.status}')"
    )