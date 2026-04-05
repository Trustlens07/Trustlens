from sqlalchemy import text
from app.core.database import SessionLocal

db = SessionLocal()
result = db.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
tables = [row[0] for row in result]
print('Tables in database:', tables)
db.close()