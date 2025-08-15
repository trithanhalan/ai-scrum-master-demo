#!/usr/bin/env python3
"""
Demo test script to verify the AI Scrum Master MVP is working correctly.
"""

import requests
import json
from datetime import datetime, timezone
from app.config import settings

BASE_URL = "http://localhost:8000"
TEST_CLOUD_ID = settings.jira_cloud_id or "test-cloud-id"
TEST_BOARD_ID = settings.jira_board_id or "test-board-id"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    print("✅ Health check passed")

def test_version():
    """Test version endpoint"""
    print("Testing version endpoint...")
    response = requests.get(f"{BASE_URL}/version")
    assert response.status_code == 200
    assert "version" in response.json()
    print("✅ Version check passed")

def test_insights():
    """Test insights endpoint"""
    print("Testing insights endpoint...")
    response = requests.get(f"{BASE_URL}/insights/sprint?boardId={TEST_BOARD_ID}&cloudId={TEST_CLOUD_ID}")
    assert response.status_code == 200
    data = response.json()
    expected_keys = ["completed", "remaining", "contributors", "scope_changes", "burndown"]
    for key in expected_keys:
        assert key in data
    print("✅ Sprint insights check passed")

def test_auth_start():
    """Test auth start endpoint"""
    print("Testing auth start endpoint...")
    response = requests.get(f"{BASE_URL}/auth/start")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("✅ Auth start check passed")

def test_openapi_docs():
    """Test OpenAPI documentation is accessible"""
    print("Testing OpenAPI docs...")
    response = requests.get(f"{BASE_URL}/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    assert "openapi" in openapi_spec
    assert "paths" in openapi_spec
    
    # Check that all expected endpoints are documented
    paths = openapi_spec["paths"]
    expected_paths = ["/healthz", "/version", "/", "/insights/sprint", "/auth/start"]
    for path in expected_paths:
        assert path in paths, f"Path {path} not found in OpenAPI spec"
    
    print("✅ OpenAPI documentation check passed")

def main():
    """Run all tests"""
    print("🚀 Starting AI Scrum Master MVP Tests...")
    print("=" * 50)
    
    try:
        test_health()
        test_version()
        test_insights()
        test_auth_start()
        test_openapi_docs()
        
        print("=" * 50)
        print("🎉 All tests passed! AI Scrum Master MVP is working correctly.")
        print()
        print("Available endpoints:")
        print("- Backend API: http://localhost:8000/docs")
        print("- Health: http://localhost:8000/healthz")
        print(f"- Sprint Insights: http://localhost:8000/insights/sprint?boardId={TEST_BOARD_ID}&cloudId={TEST_CLOUD_ID}")
        print("- Auth Start: http://localhost:8000/auth/start")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())