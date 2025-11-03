#!/usr/bin/env python3
"""
Manual test script for API endpoints.
"""

import asyncio
import json
import requests
from uuid import uuid4

BASE_URL = "http://localhost:8000"


def test_health_endpoint():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_api_v1_health():
    """Test the API v1 health endpoint."""
    print("\nTesting API v1 health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_validate_endpoint():
    """Test the SQL validation endpoint."""
    print("\nTesting SQL validation endpoint...")
    try:
        test_data = {
            "sql": "SELECT * FROM users WHERE id = 1",
            "database_id": str(uuid4()),
            "database_type": "postgresql",
        }

        response = requests.post(f"{BASE_URL}/api/v1/validate", json=test_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_tables_endpoint():
    """Test the tables listing endpoint."""
    print("\nTesting tables listing endpoint...")
    try:
        database_id = str(uuid4())
        response = requests.get(f"{BASE_URL}/api/v1/tables/{database_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_feedback_endpoint():
    """Test the feedback submission endpoint."""
    print("\nTesting feedback submission endpoint...")
    try:
        test_data = {
            "user_id": "test_user_123",
            "query_id": str(uuid4()),
            "original_query": "Show me all users",
            "generated_sql": "SELECT * FROM users",
            "feedback_type": "accept",
            "comments": "Great query!",
            "rating": 5,
        }

        response = requests.post(f"{BASE_URL}/api/v1/feedback", json=test_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Run all endpoint tests."""
    print("Starting manual endpoint tests...")
    print("=" * 50)

    tests = [
        test_health_endpoint,
        test_api_v1_health,
        test_validate_endpoint,
        test_tables_endpoint,
        test_feedback_endpoint,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print(f"Passed: {sum(results)}/{len(results)}")
    print(f"Failed: {len(results) - sum(results)}/{len(results)}")

    if all(results):
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

    return all(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
