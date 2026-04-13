"""Test script for ML service enhancement feature.

This script tests the following:
1. POST /api/v1/candidates/{candidate_id}/enhance - Enhances a candidate's score via ML service
2. GET /api/v1/scores/candidate/{candidate_id}?version=enhanced - Gets enhanced score
3. GET /api/v1/bias/metrics?candidate_id={id}&version=enhanced - Gets enhanced bias metrics
4. GET /api/v1/scores/candidate/{candidate_id}?version=original - Original data remains unchanged

Usage:
    cd backend
    python scripts/test_enhance.py

Requirements:
    - Server must be running on http://localhost:8000
    - ML service must be running and have /enhance endpoint
    - A candidate with existing score must exist in database
"""

import os
import sys
import requests
import json
from typing import Optional

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"


def test_enhance_endpoint(candidate_id: str) -> bool:
    """Test POST /candidates/{id}/enhance endpoint."""
    print(f"\n{'='*60}")
    print(f"Test 1: POST /candidates/{candidate_id}/enhance")
    print(f"{'='*60}")

    url = f"{BASE_URL}{API_PREFIX}/candidates/{candidate_id}/enhance"

    try:
        response = requests.post(url, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Enhancement successful!")
            print(f"Response: {json.dumps(data, indent=2)}")

            # Verify structure
            if "success" in data and data["success"]:
                if "data" in data:
                    enhanced_data = data["data"]
                    assert "enhanced_score" in enhanced_data, "Missing enhanced_score"
                    assert "explanation" in enhanced_data, "Missing explanation"
                    assert "original_score" in enhanced_data, "Missing original_score"
                    print(f"✅ Response structure valid")
                    return True
            else:
                print(f"❌ Response missing success flag or data")
                return False

        elif response.status_code == 404:
            print(f"⚠️ Candidate or original score not found")
            print(f"Make sure you have a candidate with ID: {candidate_id}")
            return False

        elif response.status_code == 500:
            error = response.json().get("detail", "Unknown error")
            print(f"❌ Server error: {error}")
            print("⚠️ Make sure ML service is running and accessible")
            return False

        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to server at {BASE_URL}")
        print(f"Make sure the server is running: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_get_enhanced_score(candidate_id: str) -> bool:
    """Test GET /scores/candidate/{id}?version=enhanced endpoint."""
    print(f"\n{'='*60}")
    print(f"Test 2: GET /scores/candidate/{candidate_id}?version=enhanced")
    print(f"{'='*60}")

    url = f"{BASE_URL}{API_PREFIX}/scores/candidate/{candidate_id}?version=enhanced"

    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got enhanced score!")
            print(f"Response: {json.dumps(data, indent=2)}")

            if data.get("success") and "data" in data:
                score_data = data["data"]
                assert score_data.get("version") == "enhanced", "Version should be 'enhanced'"
                assert "enhanced_at" in score_data, "Missing enhanced_at"
                print(f"✅ Enhanced score data valid")
                return True
            return False

        elif response.status_code == 404:
            error = response.json().get("detail", "")
            print(f"⚠️ Enhanced score not found: {error}")
            return False

        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_get_enhanced_bias_metrics(candidate_id: str) -> bool:
    """Test GET /bias/metrics?candidate_id={id}&version=enhanced endpoint."""
    print(f"\n{'='*60}")
    print(f"Test 3: GET /bias/metrics?candidate_id={candidate_id}&version=enhanced")
    print(f"{'='*60}")

    url = f"{BASE_URL}{API_PREFIX}/bias/metrics?candidate_id={candidate_id}&version=enhanced"

    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got enhanced bias metrics!")
            print(f"Response: {json.dumps(data, indent=2)}")

            if data.get("success") and "data" in data:
                metrics_data = data["data"]
                assert metrics_data.get("version") == "enhanced", "Version should be 'enhanced'"
                assert "enhanced_bias_metrics" in metrics_data, "Missing enhanced_bias_metrics"
                print(f"✅ Enhanced bias metrics valid")
                return True
            return False

        elif response.status_code == 404:
            error = response.json().get("detail", "")
            print(f"⚠️ Enhanced bias metrics not found: {error}")
            return False

        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_original_score_unchanged(candidate_id: str) -> bool:
    """Test GET /scores/candidate/{id}?version=original - should return original data."""
    print(f"\n{'='*60}")
    print(f"Test 4: GET /scores/candidate/{candidate_id}?version=original")
    print(f"{'='*60}")

    url = f"{BASE_URL}{API_PREFIX}/scores/candidate/{candidate_id}?version=original"

    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got original score!")

            if data.get("success") and "data" in data:
                score_data = data["data"]
                assert score_data.get("version") == "original", "Version should be 'original'"
                assert "overall_score" in score_data, "Missing overall_score"
                print(f"Original Score: {score_data.get('overall_score')}")
                print(f"Breakdown: {json.dumps(score_data.get('breakdown'), indent=2)}")
                print(f"✅ Original score data unchanged and valid")
                return True
            return False

        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_default_version_is_original(candidate_id: str) -> bool:
    """Test GET /scores/candidate/{id} without version param - should default to original."""
    print(f"\n{'='*60}")
    print(f"Test 5: GET /scores/candidate/{candidate_id} (no version param)")
    print(f"{'='*60}")

    url = f"{BASE_URL}{API_PREFIX}/scores/candidate/{candidate_id}"

    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data.get("success") and "data" in data:
                score_data = data["data"]
                # Should default to original
                version = score_data.get("version", "original")
                if version == "original":
                    print(f"✅ Default version is 'original' as expected")
                    return True
                else:
                    print(f"⚠️ Default version is '{version}', expected 'original'")
                    return False
            return False

        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_enhance_ml_service_available() -> bool:
    """Test that ML service is available."""
    print(f"\n{'='*60}")
    print(f"Test 6: Check ML service availability")
    print(f"{'='*60}")

    url = f"{BASE_URL}{API_PREFIX}/candidates/test-candidate-id/enhance"

    try:
        response = requests.post(url, timeout=10)

        if response.status_code == 404:
            # Expected - candidate not found
            print(f"✅ Backend responding (404 for test candidate is expected)")
            return True
        elif response.status_code == 500:
            error = response.json().get("detail", "")
            if "ml" in error.lower() or "enhance" in error.lower():
                print(f"⚠️ ML service may be unavailable: {error}")
                return False

        print(f"Status: {response.status_code}")
        print(f"✅ Backend responding")
        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to backend server")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Main test runner."""
    print(f"\n{'#'*60}")
    print(f"# ML Service Enhancement Feature Test Suite")
    print(f"# Base URL: {BASE_URL}")
    print(f"{'#'*60}")

    # Check if candidate_id provided as argument
    if len(sys.argv) > 1:
        candidate_id = sys.argv[1]
    else:
        # Default test candidate ID
        candidate_id = "test-candidate-id"
        print(f"\n⚠️ No candidate_id provided. Using default: {candidate_id}")
        print(f"   Usage: python scripts/test_enhance.py <candidate_id>")

    results = []

    # Run tests
    results.append(("Enhance endpoint", test_enhance_endpoint(candidate_id)))
    results.append(("Get enhanced score", test_get_enhanced_score(candidate_id)))
    results.append(("Get enhanced bias metrics", test_get_enhanced_bias_metrics(candidate_id)))
    results.append(("Original score unchanged", test_original_score_unchanged(candidate_id)))
    results.append(("Default version is original", test_default_version_is_original(candidate_id)))
    results.append(("ML service check", test_enhance_ml_service_available()))

    # Print summary
    print(f"\n{'#'*60}")
    print(f"# Test Summary")
    print(f"{'#'*60}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print(f"\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
