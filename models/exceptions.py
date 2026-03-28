class InvalidTransactionException(Exception):
  """Base exception for all transaction validation failures"""

  def __init__(self, error_code: str, message: str) -> None:
    self.error_code = error_code
    super().__init__(message)


class InsufficientBalanceException(InvalidTransactionException):
  """Raised when a debit transaction exceeds account balance"""

  def __init__(self, amount: float, balance: float) -> None:
    super().__init__(
        error_code="INSUFFICIENT_BALANCE",
        message=f"Amount ₹{amount:,.2f} exceeds balance ₹{balance:,.2f}",
    )


class CreditLimitExceededException(InvalidTransactionException):
  """Raised when a credit transaction exceeds the credit limit"""

  def __init__(self, amount: float, limit: float) -> None:
    super().__init__(
        error_code="CREDIT_LIMIT_EXCEEDED",
        message=f"Amount ₹{amount:,.2f} exceeds credit limit ₹{limit:,.2f}",
    )