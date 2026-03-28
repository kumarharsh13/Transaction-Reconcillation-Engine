from models.transaction import Transaction

class TransactionResult:
  def __init__(self, transaction: Transaction, success: bool, error_message="") -> None:
    self.transaction = transaction
    self.success = success
    self.error_message = error_message

  def __str__(self) -> str:
    if self.success:
      return f"✅ {self.transaction} - {self.error_message}"
    return f"❌ {self.transaction} - {self.error_message}"
