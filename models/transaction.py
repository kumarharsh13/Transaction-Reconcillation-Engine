from enum import Enum

from models.exceptions import (
  CreditLimitExceededException,
  InsufficientBalanceException,
  InvalidTransactionException
)

class TransactionStatus(Enum):
  PENDING = "PENDING"
  COMPLETED = "COMPLETED"
  FAILED = "FAILED"
  REVERSED = "REVERSED"

  def is_terminal(self) -> bool:
    return self in (
      TransactionStatus.COMPLETED,
      TransactionStatus.FAILED,
      TransactionStatus.REVERSED
    )

class Transaction:
  def __init__(self, id: str, amount: float, status: TransactionStatus, currency: str, created_at: str) -> None:
    self.id = id
    self.amount = amount
    self.status = status
    self.currency = currency
    self.created_at = created_at

  def __str__(self) -> str:
    return (f"{self.id} | " f"₹{self.amount:,.2f} | " f"{self.currency} | " f"{self.status.value}")

  def __repr__(self):
    return (
      f"Transaction(id='{self.id}', amount={self.amount}, "
      f"currency='{self.currency}', status={self.status})"
    )
  
  def validate(self) -> None:
    if self.amount <= 0:
      raise InvalidTransactionException(
          error_code="INVALID_AMOUNT",
          message=f"Amount must be positive, got {self.amount}",
      )
  
class CreditTransaction(Transaction):
  def __init__(self, id: str, amount: float, status: TransactionStatus, currency: str, created_at: str, credit_limit: float = 100_000.0) -> None:
    super().__init__(id, amount, status, currency, created_at)
    self.credit_limit = credit_limit

  def __str__(self):
    return f"[CREDIT] {super().__str__()}"

  def __repr__(self) -> str:
    return (
      f"CreditTransaction(id='{self.id}', amount={self.amount}, "
      f"credit_limit={self.credit_limit})"
    )
  
  def validate(self) -> None:
    super().validate() 
    if self.amount > self.credit_limit:
      raise CreditLimitExceededException(self.amount, self.credit_limit)
  
class DebitTransaction(Transaction):
  def __init__(self, id: str, amount: float, status: TransactionStatus, currency: str, created_at: str, account_balance: float = 50_000.00) -> None:
    super().__init__(id, amount, status, currency, created_at)
    self.account_balance = account_balance

  def __str__(self):
    return f"[DEBIT] {super().__str__()}"

  def __repr__(self) -> str:
    return (
      f"DebitTransaction(id='{self.id}', amount={self.amount}, "
      f"account_balance={self.account_balance})"
    )
  
  def validate(self) -> None:
    super().validate() 
    if self.amount > self.account_balance:
      raise InsufficientBalanceException(self.amount, self.account_balance)
