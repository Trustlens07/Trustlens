from app.services.storage_service import storage_service

print("=" * 60)
print("STORAGE SERVICE TEST")
print("=" * 60)

# Test the StorageService which handles uploads correctly
try:
    storage_service.ensure_bucket_exists()
    print("✓ Bucket verified")
except Exception as e:
    print(f"✗ Bucket check failed: {e}")

# Test uploading a PDF file
print("\nTesting file upload via StorageService...")
try:
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000102 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
149
%%EOF"""
    
    result = storage_service.upload_file(
        file_content=pdf_content,
        original_filename="test_resume.pdf",
        content_type="application/pdf"
    )
    
    print("✓ File uploaded successfully!")
    print(f"  File path: {result['file_path']}")
    print(f"  File URL: {result['file_url']}")
    print(f"  File size: {result['file_size']} bytes")
    
except Exception as e:
    print(f"✗ Upload failed: {e}")

print("=" * 60)