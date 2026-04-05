# test_supabase.py
from app.core.supabase_client import supabase_client

try:
    client = supabase_client.get_client()
    print("✅ Supabase client initialized successfully!")
    
    # Test auth (just checking if client works)
    print(f"✅ Supabase URL: {client.supabase_url}")
    
except Exception as e:
    print(f"❌ Supabase client failed: {e}")