#!/usr/bin/env python3
"""
Enhanced API test script for the AI Scrum Master MVP.
Tests all new endpoints and features.
"""

import requests
import json
from datetime import datetime
from app.config import settings

BASE_URL = "http://localhost:8001"
TEST_CLOUD_ID = settings.jira_cloud_id or "test-cloud-id"
TEST_BOARD_ID = settings.jira_board_id or "test-board-id"

def test_health_and_version():
    """Test basic health and version endpoints"""
    print("🔍 Testing health and version endpoints...")
    
    # Health check
    response = requests.get(f"{BASE_URL}/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    print("  ✅ Health check passed")
    
    # Version check
    response = requests.get(f"{BASE_URL}/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "environment" in data
    print("  ✅ Version check passed")

def test_metrics_endpoint():
    """Test Prometheus metrics endpoint"""
    print("🔍 Testing metrics endpoint...")
    
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200
    
    # Check that it's Prometheus format
    content = response.text
    assert "# HELP" in content
    assert "# TYPE" in content
    print("  ✅ Metrics endpoint working")

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("🔍 Testing authentication endpoints...")
    
    # Auth status without cloud_id
    response = requests.get(f"{BASE_URL}/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] == False
    assert "message" in data
    print("  ✅ Auth status (no cloud_id) working")
    
    # Auth status with fake cloud_id
    response = requests.get(f"{BASE_URL}/auth/status?cloud_id=fake-cloud-id")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] == False
    print("  ✅ Auth status (fake cloud_id) working")
    
    # Start Jira auth
    response = requests.get(f"{BASE_URL}/auth/jira/login")
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "state" in data
    print("  ✅ Jira OAuth start working")

def test_summarize_endpoints():
    """Test all summarize endpoints"""
    print("🔍 Testing summarize endpoints...")
    
    # Standup summary (should fail with no token)
    response = requests.get(f"{BASE_URL}/summarize/standup?cloudId={TEST_CLOUD_ID}")
    assert response.status_code == 404
    assert "No token found for Jira instance" in response.json()["detail"]
    print("  ✅ Standup summary (no token) working")
    
    # Blockers analysis (should fail with no token)
    response = requests.get(f"{BASE_URL}/summarize/blockers?cloudId={TEST_CLOUD_ID}")
    assert response.status_code == 404
    assert "No token found for Jira instance" in response.json()["detail"]
    print("  ✅ Blockers analysis (no token) working")
    
    # Retrospective (should work without accountId, but may fail with invalid API key)
    response = requests.get(f"{BASE_URL}/summarize/retrospective?boardId=123")
    # Accept both success and OpenAI API key error
    assert response.status_code in [200, 500]
    data = response.json()
    if response.status_code == 200:
        assert "retrospective" in data
        assert "board_id" in data
        print("  ✅ Retrospective (no auth) working")
    else:
        # Check if it's an OpenAI API key error
        assert "OpenAI" in str(data) or "API key" in str(data)
        print("  ✅ Retrospective (API key error expected) working")

def test_insights_endpoint():
    """Test insights endpoints"""
    print("🔍 Testing insights endpoints...")
    
    response = requests.get(f"{BASE_URL}/insights/sprint?boardId={TEST_BOARD_ID}&cloudId={TEST_CLOUD_ID}")
    assert response.status_code == 200
    data = response.json()
    expected_keys = ["completed", "remaining", "contributors", "scope_changes", "burndown"]
    for key in expected_keys:
        assert key in data
    print("  ✅ Sprint insights working")

def test_openapi_documentation():
    """Test OpenAPI documentation"""
    print("🔍 Testing OpenAPI documentation...")
    
    response = requests.get(f"{BASE_URL}/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    assert "openapi" in openapi_spec
    assert "paths" in openapi_spec
    
    # Check that new endpoints are documented
    paths = openapi_spec["paths"]
    expected_paths = [
        "/healthz", "/version", "/metrics", "/",
        "/auth/jira/login", "/auth/callback", "/auth/status",
        "/summarize/standup", "/summarize/blockers", "/summarize/retrospective",
        "/insights/sprint"
    ]
    
    for path in expected_paths:
        assert path in paths, f"Path {path} not found in OpenAPI spec"
    
    print("  ✅ OpenAPI documentation complete")

def test_error_handling():
    """Test error handling"""
    print("🔍 Testing error handling...")
    
    # Invalid endpoint
    response = requests.get(f"{BASE_URL}/nonexistent")
    assert response.status_code == 404
    print("  ✅ 404 error handling working")
    
    # Missing required parameters
    response = requests.get(f"{BASE_URL}/summarize/standup")
    assert response.status_code == 422  # Validation error
    print("  ✅ Parameter validation working")

def main():
    """Run all tests"""
    print("🚀 Starting Enhanced AI Scrum Master API Tests...")
    print("=" * 60)
    
    try:
        test_health_and_version()
        test_metrics_endpoint()
        test_auth_endpoints()
        test_summarize_endpoints()
        test_insights_endpoint()
        test_openapi_documentation()
        test_error_handling()
        
        print("=" * 60)
        print("🎉 All enhanced API tests passed!")
        print()
        print("📋 Available endpoints:")
        print("  • Backend API: http://localhost:8001/docs")
        print("  • Metrics: http://localhost:8001/metrics")
        print("  • Auth Status: http://localhost:8001/auth/status")
        print("  • Start Jira OAuth: http://localhost:8001/auth/jira/login")
        print("  • Standup Summary: http://localhost:8001/summarize/standup")
        print("  • Blockers Analysis: http://localhost:8001/summarize/blockers")
        print("  • Retrospective: http://localhost:8001/summarize/retrospective")
        print("  • Sprint Insights: http://localhost:8001/insights/sprint")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())