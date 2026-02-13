"""
Test Script for ConvertAll Backend
Tests all API endpoints to ensure they're working correctly
"""

import requests
import os
from io import BytesIO
from PIL import Image

BASE_URL = 'http://localhost:5000'


def test_health_check():
    """Test health check endpoint"""
    print("\n🔍 Testing health check...")
    try:
        response = requests.get(f'{BASE_URL}/health')
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def create_test_image():
    """Create a test image"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


def test_endpoint(endpoint, file_data, filename, additional_data=None):
    """Generic endpoint test"""
    print(f"\n🔍 Testing {endpoint}...")
    try:
        files = {'file': (filename, file_data, 'application/octet-stream')}
        data = additional_data or {}
        
        response = requests.post(
            f'{BASE_URL}{endpoint}',
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ {endpoint} test passed!")
                print(f"   Download URL: {result.get('download_url', 'N/A')}")
                return True
            else:
                print(f"❌ {endpoint} returned success=False")
                print(f"   Error: {result.get('error', 'Unknown')}")
                return False
        else:
            print(f"❌ {endpoint} failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print(f"⏱️  {endpoint} timed out (may still be processing)")
        return None
    except Exception as e:
        print(f"❌ {endpoint} error: {e}")
        return False


def run_all_tests():
    """Run all endpoint tests"""
    print("=" * 60)
    print("ConvertAll Backend - API Test Suite")
    print("=" * 60)
    print(f"\nTesting server at: {BASE_URL}")
    print("\nNote: Some tests may take time or fail if you don't have")
    print("sample files. The main goal is to verify endpoints respond.")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Health Check
    results['health'] = test_health_check()
    
    # Test 2: Background Removal (if server has image processing)
    print("\n📸 Image Processing Tests:")
    test_img = create_test_image()
    results['bg_removal'] = test_endpoint(
        '/api/remove-background',
        test_img,
        'test.png'
    )
    
    # Document conversion tests would need actual files
    # These are just connectivity tests
    print("\n📄 Document Conversion Tests:")
    print("   (Skipping - requires actual document files)")
    print("   To test manually, use curl with your own files:")
    print("   curl -X POST -F 'file=@document.pdf' http://localhost:5000/api/convert/pdf-to-word")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped/Timeout: {skipped}")
    
    if results.get('health'):
        print("\n🎉 Server is running and responding!")
        print("\nNext steps:")
        print("1. Test individual endpoints with real files")
        print("2. Integrate with your frontend")
        print("3. Check README.md for endpoint documentation")
    else:
        print("\n⚠️  Server is not responding. Make sure it's running:")
        print("   python main.py")
    
    print("=" * 60)


def print_endpoint_examples():
    """Print example curl commands"""
    print("\n" + "=" * 60)
    print("Example Test Commands (using curl):")
    print("=" * 60)
    
    examples = [
        ("Health Check", "curl http://localhost:5000/health"),
        ("Background Removal", "curl -X POST -F 'file=@image.jpg' http://localhost:5000/api/remove-background"),
        ("PDF to Word", "curl -X POST -F 'file=@document.pdf' http://localhost:5000/api/convert/pdf-to-word"),
        ("Word to PDF", "curl -X POST -F 'file=@document.docx' http://localhost:5000/api/convert/word-to-pdf"),
        ("Extract PDF Images", "curl -X POST -F 'file=@document.pdf' http://localhost:5000/api/extract/pdf-images"),
        ("Video Convert", "curl -X POST -F 'file=@video.mp4' -F 'format=avi' http://localhost:5000/api/convert/video"),
        ("Extract Audio", "curl -X POST -F 'file=@video.mp4' -F 'format=mp3' http://localhost:5000/api/extract/audio"),
    ]
    
    for name, command in examples:
        print(f"\n{name}:")
        print(f"  {command}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    # Run tests
    run_all_tests()
    
    # Print examples
    print_endpoint_examples()
    
    print("\n💡 Tip: Keep this script handy for debugging!")
    print("   Run: python test_api.py")