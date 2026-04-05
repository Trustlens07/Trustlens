# test_storage.py
from app.services.storage_service import storage_service

try:
    # Ensure bucket exists
    storage_service.ensure_bucket_exists()
    print("✅ Storage bucket verified/created successfully!")
    
    # List buckets (optional)
    client = storage_service.client.get_client()
    buckets = client.storage().list_buckets()
    print(f"✅ Available buckets: {[b.name for b in buckets]}")
    
except Exception as e:
    print(f"❌ Storage verification failed: {e}")