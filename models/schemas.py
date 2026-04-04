from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum

class TransactionType(str, Enum):
  CREDIT = "CREDIT"
  DEBIT = "DEBIT"

class TransactionStatusEnum(str, Enum):
  PENDING = "PENDING"
  COMPLETED = "COMPLETED"
  FAILED = "FAILED"
  REVERSED = "REVERSED"

# ──────────────────────────────────────────────────
# Request schemas — what comes IN from the API user
# ──────────────────────────────────────────────────

class TransactionCreate(BaseModel):
  amount: float = Field(
    gt=0,
    description="Transaction amount, must be positive",
    examples=[5000.00],
  )
  currency: str = Field(
    min_length=3,
    max_length=3,
    description="3-letter currency code",
    examples=["INR"],
  )
  type: TransactionType = Field(
    description="CREDIT or DEBIT",
    examples=["CREDIT"],
  )

  # Optional fields with defaults
  credit_limit: Optional[float] = Field(
    default=None,
    gt=0,
    description="Credit limit (only for CREDIT type)",
  )
  account_balance: Optional[float] = Field(
    default=None,
    gt=0,
    description="Account balance (only for DEBIT type)",
  )

    # ── Custom validators ──────────────────────
    # These run AFTER Pydantic's built-in type checks

  @field_validator("currency")
  @classmethod
  def currency_must_be_valid(cls, v: str) -> str:
    allowed = {"INR", "USD", "EUR", "GBP"}
    if v.upper() not in allowed:
        raise ValueError(f"Currency must be one of {allowed}, got '{v}'")
    return v.upper()  # normalize to uppercase

  @field_validator("type")
  @classmethod
  def credit_debit_fields_check(cls, v, info):
    return v

class TransactionUpdate(BaseModel):
  status: Optional[TransactionStatusEnum] = None
  amount: Optional[float] = Field(default=None, gt=0)
  currency: Optional[str] = Field(default=None, min_length=3, max_length=3)

# ──────────────────────────────────────────────────
# Response schemas — what goes OUT to the API user
# ──────────────────────────────────────────────────
class TransactionResponse(BaseModel):
  id: str
  amount: float
  currency: str
  type: TransactionType
  status: TransactionStatusEnum
  created_at: str
  model_config = {"from_attributes": True}

class ProcessingSummary(BaseModel):
  total: int
  completed: int
  failed: int
  success_rate: float
  total_amount: float
  by_currency: dict[str, int]

class ErrorResponse(BaseModel):
  detail: str
  error_code: Optional[str] = None

class BatchTransactionCreate(BaseModel):
  transactions: list[TransactionCreate]

class BatchResult(BaseModel):
  total: int
  successful: int
  failed: int
  results: list[dict]

class UploadResult(BaseModel):
  total_rows: int
  parsed: int
  parse_errors: int
  created: int
  errors: list[str]