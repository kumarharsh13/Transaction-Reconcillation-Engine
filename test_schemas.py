"""
Day 8: Test Pydantic schemas
Run with: python3 -m test_schemas
"""

from pydantic import ValidationError
from models.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionType,
    TransactionStatusEnum,
)


def main():
  print("=" * 55)
  print("  PYDANTIC VALIDATION TESTS")
  print("=" * 55)

  # ── Test 1: Valid transaction ──────────────────
  print("\n1. Valid CREDIT transaction:")
  txn = TransactionCreate(
    amount=5000,
    currency="INR",
    type=TransactionType.CREDIT,
  )
  print(f"   Created: {txn}")
  print(f"   Amount: {txn.amount} (type: {type(txn.amount).__name__})")
  print(f"   Currency: {txn.currency}")

  # ── Test 2: Auto type conversion ──────────────
  print("\n2. String '5000' auto-converts to float:")
  txn = TransactionCreate(
    amount="5000",       # string, not float!
    currency="inr",      # lowercase!
    type="CREDIT",       # string, not enum!
  )
  print(f"   Amount: {txn.amount} (type: {type(txn.amount).__name__})")
  print(f"   Currency: {txn.currency}")  # auto uppercased by validator
  print(f"   Type: {txn.type}")

  # ── Test 3: Negative amount — should fail ─────
  print("\n3. Negative amount (should fail):")
  try:
    txn = TransactionCreate(
      amount=-500,
      currency="INR",
      type="CREDIT",
    )
  except ValidationError as e:
    print(f"   Caught error: {e.error_count()} validation error(s)")
    for error in e.errors():
      print(f"   → Field: {error['loc'][0]}, Error: {error['msg']}")

  # ── Test 4: Invalid currency ──────────────────
  print("\n4. Invalid currency 'XYZ' (should fail):")
  try:
    txn = TransactionCreate(
      amount=5000,
      currency="XYZ",
      type="CREDIT",
    )
  except ValidationError as e:
    for error in e.errors():
      print(f"   → Field: {error['loc'][0]}, Error: {error['msg']}")

  # ── Test 5: Missing required field ────────────
  print("\n5. Missing 'amount' field (should fail):")
  try:
    txn = TransactionCreate(
      currency="INR",
      type="CREDIT",
    )
  except ValidationError as e:
    for error in e.errors():
      print(f"   → Field: {error['loc'][0]}, Error: {error['msg']}")

  # ── Test 6: Multiple errors at once ───────────
  print("\n6. Multiple errors (negative amount + bad currency):")
  try:
    txn = TransactionCreate(
      amount=-500,
      currency="INVALID",
      type="CREDIT",
    )
  except ValidationError as e:
    print(f"   Caught {e.error_count()} errors:")
    for error in e.errors():
      print(f"   → {error['loc'][0]}: {error['msg']}")

  # ── Test 7: TransactionResponse ───────────────
  print("\n7. Response schema:")
  response = TransactionResponse(
    id="TXN001",
    amount=5000,
    currency="INR",
    type=TransactionType.CREDIT,
    status=TransactionStatusEnum.COMPLETED,
    created_at="2025-01-15",
  )

  print(f"   {response}")
  # Convert to dict (this is what FastAPI sends as JSON)
  print(f"   As dict: {response.model_dump()}")
  # Convert to JSON string
  print(f"   As JSON: {response.model_dump_json()}")

  # ── Test 8: TransactionUpdate (partial) ───────
  print("\n8. Partial update (only status):")
  update = TransactionUpdate(status=TransactionStatusEnum.COMPLETED)
  print(f"   {update}")
  print(f"   Only changed fields: {update.model_dump(exclude_none=True)}")

  # ── Test 9: Construct from dict ───────────────
  print("\n9. Create from dict (like parsing JSON request body):")
  raw_data = {
      "amount": 7500,
      "currency": "USD",
      "type": "DEBIT",
      "account_balance": 50000,
  }
  txn = TransactionCreate(**raw_data)
  # **raw_data unpacks the dict into keyword arguments
  # Same as: TransactionCreate(amount=7500, currency="USD", type="DEBIT", ...)
  print(f"   Created from dict: {txn}")

  print("\n" + "=" * 55)
  print("  ALL TESTS PASSED")
  print("=" * 55)


if __name__ == "__main__":
  main()