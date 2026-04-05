from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://localhost/transaction_engine"

# ── Engine ────────────────────────────────────────
# Engine = the actual connection to PostgreSQL
# Like opening a connection pool to the database

engine = create_engine(DATABASE_URL, echo=True)

# ── Session Factory ───────────────────────────────
# SessionLocal creates new database sessions
# A session = one "conversation" with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Base Class ────────────────────────────────────
# All your models will inherit from this
Base = declarative_base()

def get_db():
  """
  Creates a new database session for each request.
  Closes it when the request is done.

  This is a 'dependency' — FastAPI calls it automatically
  for every endpoint that needs a database connection.
  """
  db = SessionLocal()
  try:
    yield db
    # 'yield' means: give this session to the endpoint
    # When the endpoint finishes, come back here
  finally:
    db.close()