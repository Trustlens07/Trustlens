# test_tables.py
from app.core.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

print("Tables in database:")
required_tables = ['candidates', 'scores', 'bias_metrics', 'feedback']

for table in required_tables:
    if table in tables:
        print(f"✅ {table} table exists")
        
        # Show columns
        columns = inspector.get_columns(table)
        print(f"   Columns: {', '.join([col['name'] for col in columns[:5]])}")
    else:
        print(f"❌ {table} table missing")

print(f"\nTotal tables: {len(tables)}")