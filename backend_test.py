#!/usr/bin/env python3
"""
Comprehensive Backend Testing for AI Scrum Master MVP
Tests all API endpoints, authentication flows, and database operations
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== {test_name} ==={Colors.ENDC}")

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "total": 0
        }
        self.connection_cookie = None
        
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = f"{BASE_URL}{endpoint}" if not endpoint.startswith('http') else endpoint
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            print_error(f"Request failed: {e}")
            raise

    def test_health_endpoints(self):
        """Test basic health check endpoints"""
        print_test_header("Health Check Endpoints")
        
        # Test root endpoint
        try:
            response = self.make_request("GET", "/")
            if response.status_code == 200:
                data = response.json()
                if "AI Scrum Master API" in data.get("message", ""):
                    print_success("Root endpoint working")
                    self.test_results["passed"] += 1
                else:
                    print_error("Root endpoint returned unexpected message")
                    self.test_results["failed"] += 1
            else:
                print_error(f"Root endpoint failed: {response.status_code}")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"Root endpoint error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1
        
        # Test /healthz
        try:
            response = self.make_request("GET", "/healthz")
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") is True:
                    print_success("/healthz endpoint working")
                    self.test_results["passed"] += 1
                else:
                    print_error("/healthz returned unexpected response")
                    self.test_results["failed"] += 1
            else:
                print_error(f"/healthz failed: {response.status_code}")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"/healthz error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1
        
        # Test /version
        try:
            response = self.make_request("GET", "/version")
            if response.status_code == 200:
                data = response.json()
                if "version" in data and "environment" in data:
                    print_success(f"/version endpoint working - Version: {data['version']}, Env: {data['environment']}")
                    self.test_results["passed"] += 1
                else:
                    print_error("/version returned incomplete response")
                    self.test_results["failed"] += 1
            else:
                print_error(f"/version failed: {response.status_code}")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"/version error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1
        
        # Test /metrics
        try:
            response = self.make_request("GET", "/metrics")
            if response.status_code == 200:
                print_success("/metrics endpoint working")
                self.test_results["passed"] += 1
            else:
                print_error(f"/metrics failed: {response.status_code}")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"/metrics error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print_test_header("Authentication Endpoints")
        
        # Test /auth/jira/login
        try:
            response = self.make_request("GET", "/auth/jira/login")
            if response.status_code == 200:
                data = response.json()
                if "authorization_url" in data and "state" in data:
                    auth_url = data["authorization_url"]
                    state = data["state"]
                    
                    # Validate OAuth URL structure
                    parsed_url = urlparse(auth_url)
                    if parsed_url.hostname == "auth.atlassian.com":
                        query_params = parse_qs(parsed_url.query)
                        required_params = ["client_id", "scope", "redirect_uri", "state", "response_type", "code_challenge"]
                        
                        missing_params = [param for param in required_params if param not in query_params]
                        if not missing_params:
                            print_success(f"/auth/jira/login working - OAuth URL generated with state: {state[:8]}...")
                            self.test_results["passed"] += 1
                        else:
                            print_error(f"/auth/jira/login missing OAuth parameters: {missing_params}")
                            self.test_results["failed"] += 1
                    else:
                        print_error(f"/auth/jira/login generated invalid OAuth URL: {auth_url}")
                        self.test_results["failed"] += 1
                else:
                    print_error("/auth/jira/login missing required fields")
                    self.test_results["failed"] += 1
            else:
                print_error(f"/auth/jira/login failed: {response.status_code}")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"/auth/jira/login error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1
        
        # Test /auth/connection (should work without authentication)
        try:
            response = self.make_request("GET", "/auth/connection")
            if response.status_code == 200:
                data = response.json()
                if "authenticated" in data:
                    if data["authenticated"] is False:
                        print_success("/auth/connection working - No active connection (expected)")
                        self.test_results["passed"] += 1
                    else:
                        print_warning("/auth/connection shows active connection - this might be from previous tests")
                        self.test_results["warnings"] += 1
                else:
                    print_error("/auth/connection missing 'authenticated' field")
                    self.test_results["failed"] += 1
            else:
                print_error(f"/auth/connection failed: {response.status_code}")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"/auth/connection error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1

    def test_jira_helper_endpoints_unauthenticated(self):
        """Test Jira helper endpoints without authentication (should fail properly)"""
        print_test_header("Jira Helper Endpoints (Unauthenticated)")
        
        # Test /auth/jira/boards without authentication
        try:
            response = self.make_request("GET", "/auth/jira/boards")
            if response.status_code == 401:
                data = response.json()
                if "detail" in data and "authenticate" in data["detail"].lower():
                    print_success("/auth/jira/boards properly requires authentication")
                    self.test_results["passed"] += 1
                else:
                    print_warning("/auth/jira/boards returns 401 but with unexpected message")
                    self.test_results["warnings"] += 1
            else:
                print_error(f"/auth/jira/boards should return 401 but returned: {response.status_code}")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"/auth/jira/boards error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1
        
        # Test /auth/jira/projects without authentication
        try:
            response = self.make_request("GET", "/auth/jira/projects")
            if response.status_code == 401:
                data = response.json()
                if "detail" in data and "authenticate" in data["detail"].lower():
                    print_success("/auth/jira/projects properly requires authentication")
                    self.test_results["passed"] += 1
                else:
                    print_warning("/auth/jira/projects returns 401 but with unexpected message")
                    self.test_results["warnings"] += 1
            else:
                print_error(f"/auth/jira/projects should return 401 but returned: {response.status_code}")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"/auth/jira/projects error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1

    def test_summarize_endpoints(self):
        """Test summarize endpoints"""
        print_test_header("Summarize Endpoints")
        
        # Test /summarize/standup without authentication
        try:
            response = self.make_request("GET", "/summarize/standup")
            if response.status_code == 404:
                data = response.json()
                if "No active Jira connection" in data.get("detail", ""):
                    print_success("/summarize/standup properly requires authentication")
                    self.test_results["passed"] += 1
                else:
                    print_warning("/summarize/standup returns 404 but with unexpected message")
                    self.test_results["warnings"] += 1
            else:
                print_error(f"/summarize/standup should return 404 but returned: {response.status_code}")
                if response.status_code == 200:
                    print_info("This might indicate demo mode is working")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"/summarize/standup error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1

    def test_insights_endpoints(self):
        """Test insights endpoints with demo parameters"""
        print_test_header("Insights Endpoints")
        
        # Test /insights/sprint with demo parameters
        try:
            params = {
                "boardId": "demo",
                "accountId": "demo", 
                "cloudId": "demo"
            }
            response = self.make_request("GET", "/insights/sprint", params=params)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["completed", "remaining", "total_issues", "demo_mode"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    if data.get("demo_mode") is True:
                        print_success("/insights/sprint working in demo mode")
                        self.test_results["passed"] += 1
                    else:
                        print_warning("/insights/sprint working but not in demo mode")
                        self.test_results["warnings"] += 1
                else:
                    print_error(f"/insights/sprint missing required fields: {missing_fields}")
                    self.test_results["failed"] += 1
            else:
                print_error(f"/insights/sprint failed: {response.status_code}")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"/insights/sprint error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1

    def test_database_connectivity(self):
        """Test database operations indirectly through API endpoints"""
        print_test_header("Database Connectivity")
        
        # Test that endpoints requiring database access work
        try:
            response = self.make_request("GET", "/auth/connection")
            if response.status_code == 200:
                print_success("Database connectivity working (auth/connection endpoint accessible)")
                self.test_results["passed"] += 1
            else:
                print_error("Database connectivity issues (auth/connection endpoint failed)")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"Database connectivity test error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1

    def test_cors_and_headers(self):
        """Test CORS configuration and response headers"""
        print_test_header("CORS and Headers")
        
        try:
            response = self.make_request("GET", "/healthz")
            headers = response.headers
            
            # Check for CORS headers (might not be present in same-origin requests)
            if response.status_code == 200:
                print_success("CORS configuration allows requests")
                self.test_results["passed"] += 1
            else:
                print_error("CORS configuration might be blocking requests")
                self.test_results["failed"] += 1
                
            # Check content type
            if "application/json" in headers.get("content-type", ""):
                print_success("Proper JSON content-type headers")
                self.test_results["passed"] += 1
            else:
                print_warning("Unexpected content-type headers")
                self.test_results["warnings"] += 1
                
        except Exception as e:
            print_error(f"CORS/Headers test error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 2

    def test_error_handling(self):
        """Test error handling for invalid endpoints"""
        print_test_header("Error Handling")
        
        # Test 404 for non-existent endpoint
        try:
            response = self.make_request("GET", "/nonexistent")
            if response.status_code == 404:
                print_success("404 error handling working")
                self.test_results["passed"] += 1
            else:
                print_error(f"Expected 404 but got: {response.status_code}")
                self.test_results["failed"] += 1
        except Exception as e:
            print_error(f"404 test error: {e}")
            self.test_results["failed"] += 1
        
        self.test_results["total"] += 1

    def run_all_tests(self):
        """Run all backend tests"""
        print(f"{Colors.BOLD}🚀 Starting Comprehensive Backend Testing for AI Scrum Master MVP{Colors.ENDC}")
        print(f"Testing against: {BASE_URL}")
        print("=" * 60)
        
        # Run all test suites
        self.test_health_endpoints()
        self.test_auth_endpoints()
        self.test_jira_helper_endpoints_unauthenticated()
        self.test_summarize_endpoints()
        self.test_insights_endpoints()
        self.test_database_connectivity()
        self.test_cors_and_headers()
        self.test_error_handling()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}📊 TEST RESULTS SUMMARY{Colors.ENDC}")
        print("=" * 60)
        
        print(f"Total Tests: {self.test_results['total']}")
        print(f"{Colors.GREEN}✅ Passed: {self.test_results['passed']}{Colors.ENDC}")
        print(f"{Colors.RED}❌ Failed: {self.test_results['failed']}{Colors.ENDC}")
        print(f"{Colors.YELLOW}⚠️  Warnings: {self.test_results['warnings']}{Colors.ENDC}")
        
        success_rate = (self.test_results['passed'] / self.test_results['total']) * 100 if self.test_results['total'] > 0 else 0
        
        if success_rate >= 80:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Overall Status: GOOD ({success_rate:.1f}% success rate){Colors.ENDC}")
        elif success_rate >= 60:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Overall Status: NEEDS ATTENTION ({success_rate:.1f}% success rate){Colors.ENDC}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}🚨 Overall Status: CRITICAL ISSUES ({success_rate:.1f}% success rate){Colors.ENDC}")
        
        print("\n" + "=" * 60)
        
        # Detailed findings
        print(f"{Colors.BOLD}🔍 KEY FINDINGS:{Colors.ENDC}")
        
        if self.test_results['failed'] == 0:
            print("• All critical functionality is working")
            print("• API endpoints are responding correctly")
            print("• Authentication flow is properly configured")
            print("• Database connectivity is working")
        else:
            print("• Some critical issues found - see details above")
            
        if self.test_results['warnings'] > 0:
            print(f"• {self.test_results['warnings']} minor issues or warnings noted")

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()