from database.connection import engine, Base
from database.models import TransactionDB

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done! Tables created in PostgreSQL.")