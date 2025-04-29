"""
MOE Integration Edge Case Tests
------------------------------
This script tests edge cases and critical issue fixes for the MOE integration in the NextJS chat application.
"""

import requests
import json
import time
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

# Configuration
MOE_API_URL = "http://localhost:8000"
NEXTJS_API_URL = "http://localhost:3000/api"

class EdgeCaseTests:
    """Test class for edge cases and critical fixes"""
    
    def __init__(self):
        self.test_results = {}
    
    def test_db_connection_handling(self):
        """
        Test the improved database connection handling.
        This test sends multiple rapid requests to verify connection pooling and error handling.
        """
        print("\nTesting database connection handling...")
        
        # Create multiple chat sessions rapidly to stress test connection handling
        num_sessions = 5
        results = []
        
        with ThreadPoolExecutor(max_workers=num_sessions) as executor:
            futures = []
            for i in range(num_sessions):
                chat_id = f"db-test-{int(time.time())}-{i}"
                message = f"Test message for database connection test {i}"
                future = executor.submit(
                    self._send_chat_request, 
                    chat_id, 
                    message, 
                    "moe-auto"
                )
                futures.append(future)
                # Sleep a tiny bit to ensure different timestamps
                time.sleep(0.1)
            
            for future in futures:
                results.append(future.result())
        
        # Check results
        success_count = sum(1 for r in results if r.get("status") == "success")
        
        return {
            "total_requests": num_sessions,
            "successful_requests": success_count,
            "success_rate": success_count / num_sessions,
            "results": results
        }
    
    def test_error_handling(self):
        """
        Test improved error handling in API routes.
        Sends various malformed requests to check error responses.
        """
        print("\nTesting error handling in API routes...")
        
        test_cases = [
            # Missing required fields
            {"name": "missing_id", "payload": {
                "message": {"id": "msg-1", "role": "user", "content": "Test"},
                "selectedChatModel": "moe-auto"
                # missing id
            }},
            # Invalid model ID
            {"name": "invalid_model", "payload": {
                "id": "test-invalid-model",
                "message": {"id": "msg-2", "role": "user", "content": "Test"},
                "selectedChatModel": "non-existent-model"
            }},
            # Malformed message
            {"name": "malformed_message", "payload": {
                "id": "test-malformed",
                "message": {"role": "user", "content": "Test"},  # missing message id
                "selectedChatModel": "moe-auto"
            }},
            # Empty message
            {"name": "empty_message", "payload": {
                "id": "test-empty",
                "message": {"id": "msg-3", "role": "user", "content": ""},
                "selectedChatModel": "moe-auto"
            }}
        ]
        
        results = {}
        for test_case in test_cases:
            name = test_case["name"]
            payload = test_case["payload"]
            print(f"  Running test case: {name}")
            
            try:
                response = requests.post(f"{NEXTJS_API_URL}/chat", json=payload, timeout=10)
                results[name] = {
                    "status_code": response.status_code,
                    "response": response.text,
                    "is_error_handled": 400 <= response.status_code < 500  # Check if it's a client error
                }
            except requests.RequestException as e:
                results[name] = {
                    "error": str(e),
                    "is_error_handled": False
                }
        
        return results
    
    async def _test_streaming_response_timeout(self, timeout_secs=40):
        """
        Test a single streaming response with timeout.
        """
        chat_id = f"timeout-test-{int(time.time())}"
        payload = {
            "id": chat_id,
            "message": {
                "id": f"msg-{int(time.time())}",
                "role": "user",
                "content": "This is a very long and complex request that should take a while to process. Please analyze the following text in extreme detail and provide a comprehensive response with multiple paragraphs: " + "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 50
            },
            "selectedChatModel": "moe-auto"
        }
        
        timeout = aiohttp.ClientTimeout(total=timeout_secs)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = time.time()
                async with session.post(f"{NEXTJS_API_URL}/chat", json=payload) as response:
                    # For SSE streaming responses, we need to read until completion or timeout
                    chunks_received = 0
                    async for chunk in response.content.iter_any():
                        chunks_received += 1
                    
                    duration = time.time() - start_time
                    return {
                        "status": "completed",
                        "status_code": response.status,
                        "duration": duration,
                        "chunks_received": chunks_received,
                        "completed_before_timeout": True
                    }
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return {
                "status": "timeout",
                "duration": duration,
                "completed_before_timeout": False
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "completed_before_timeout": False
            }
    
    async def test_streaming_response_handling(self):
        """
        Test streaming response handling with timeouts.
        Tests how the system handles long-running streaming responses.
        """
        print("\nTesting streaming response handling with timeouts...")
        
        # Test with different timeouts
        timeout_results = {}
        for timeout in [15, 30]:
            print(f"  Testing with {timeout} second timeout...")
            result = await self._test_streaming_response_timeout(timeout)
            timeout_results[f"timeout_{timeout}s"] = result
        
        # Test concurrent streaming requests
        print("  Testing concurrent streaming requests...")
        concurrent_tasks = []
        for i in range(3):
            concurrent_tasks.append(self._test_streaming_response_timeout(30))
        
        concurrent_results = await asyncio.gather(*concurrent_tasks)
        
        return {
            "timeout_tests": timeout_results,
            "concurrent_tests": concurrent_results
        }
    
    def test_edge_runtime_compatibility(self):
        """
        Test Edge Runtime compatibility.
        Verifies the API can work in Vercel Edge Runtime environment.
        """
        print("\nTesting Edge Runtime compatibility...")
        
        # Send a request to verify the response headers that indicate Edge compatibility
        test_payload = {
            "id": f"edge-test-{int(time.time())}",
            "message": {
                "id": f"msg-{int(time.time())}",
                "role": "user",
                "content": "Test Edge Runtime compatibility"
            },
            "selectedChatModel": "moe-auto"
        }
        
        try:
            response = requests.post(f"{NEXTJS_API_URL}/chat", json=test_payload, timeout=15)
            
            # Check for Edge runtime headers or indicators
            headers = dict(response.headers)
            is_edge_compatible = any(h.lower() in ['x-vercel-edge', 'x-middleware-next', 'x-vercel-id'] 
                                  for h in headers.keys())
            
            return {
                "status_code": response.status_code,
                "headers": headers,
                "is_edge_compatible": is_edge_compatible,
                "supports_streaming": "text/event-stream" in response.headers.get("content-type", "")
            }
        except requests.RequestException as e:
            return {
                "error": str(e),
                "is_edge_compatible": False
            }
    
    def _send_chat_request(self, chat_id, message_text, model):
        """Helper method to send a chat request"""
        payload = {
            "id": chat_id,
            "message": {
                "id": f"msg-{int(time.time())}",
                "role": "user",
                "content": message_text
            },
            "selectedChatModel": model
        }
        
        try:
            response = requests.post(f"{NEXTJS_API_URL}/chat", json=payload, timeout=15)
            return {
                "status": "success" if response.status_code < 400 else "error",
                "status_code": response.status_code,
                "chat_id": chat_id
            }
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "chat_id": chat_id
            }
    
    async def run_all_tests(self):
        """Run all edge case tests"""
        print("Starting MOE Edge Case Tests for NextJS Chat Application")
        print("=" * 60)
        
        # Test database connection handling
        self.test_results["db_connection"] = self.test_db_connection_handling()
        
        # Test error handling
        self.test_results["error_handling"] = self.test_error_handling()
        
        # Test streaming response handling
        self.test_results["streaming"] = await self.test_streaming_response_handling()
        
        # Test Edge Runtime compatibility
        self.test_results["edge_runtime"] = self.test_edge_runtime_compatibility()
        
        print("\nAll edge case tests completed!")
        return self.test_results
    
    def print_test_summary(self):
        """Print a summary of test results"""
        if not self.test_results:
            print("No test results to display")
            return
        
        print("\n" + "=" * 60)
        print("MOE INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        # Database connection handling
        db_tests = self.test_results.get("db_connection", {})
        if db_tests:
            print("\nDatabase Connection Handling:")
            print(f"  Success Rate: {db_tests.get('success_rate', 0) * 100:.1f}%")
            print(f"  Successful Requests: {db_tests.get('successful_requests', 0)}/{db_tests.get('total_requests', 0)}")
        
        # Error handling
        error_tests = self.test_results.get("error_handling", {})
        if error_tests:
            print("\nError Handling in API Routes:")
            properly_handled = sum(1 for result in error_tests.values() if result.get("is_error_handled", False))
            print(f"  Properly Handled Errors: {properly_handled}/{len(error_tests)}")
            for name, result in error_tests.items():
                status = "✓" if result.get("is_error_handled", False) else "✗"
                print(f"  {status} {name}: {result.get('status_code', 'N/A')}")
        
        # Streaming response
        streaming_tests = self.test_results.get("streaming", {})
        if streaming_tests:
            print("\nStreaming Response Handling:")
            timeout_tests = streaming_tests.get("timeout_tests", {})
            for test_name, result in timeout_tests.items():
                status = "✓" if result.get("completed_before_timeout", False) else "✗"
                print(f"  {status} {test_name}: {result.get('status', 'unknown')}, " +
                      f"Duration: {result.get('duration', 'N/A'):.1f}s")
            
            concurrent_tests = streaming_tests.get("concurrent_tests", [])
            concurrent_success = sum(1 for r in concurrent_tests if r.get("completed_before_timeout", False))
            print(f"  Concurrent Streaming Success: {concurrent_success}/{len(concurrent_tests)}")
        
        # Edge runtime
        edge_tests = self.test_results.get("edge_runtime", {})
        if edge_tests:
            print("\nEdge Runtime Compatibility:")
            edge_compatible = edge_tests.get("is_edge_compatible", False)
            status = "✓" if edge_compatible else "✗"
            print(f"  {status} Edge Runtime Compatible")
            
            streaming = edge_tests.get("supports_streaming", False)
            status = "✓" if streaming else "✗"
            print(f"  {status} Supports Streaming in Edge Runtime")
        
        print("\nTEST SUMMARY:")
        all_passed = all([
            self.test_results.get("db_connection", {}).get("success_rate", 0) > 0.8,
            sum(1 for r in self.test_results.get("error_handling", {}).values() 
                if r.get("is_error_handled", False)) == len(self.test_results.get("error_handling", {})),
            any(r.get("completed_before_timeout", False) 
                for r in self.test_results.get("streaming", {}).get("timeout_tests", {}).values()),
            self.test_results.get("edge_runtime", {}).get("is_edge_compatible", False)
        ])
        
        if all_passed:
            print("✅ All critical issues appear to be fixed!")
        else:
            print("❌ Some critical issues may still need attention.")


async def main():
    tests = EdgeCaseTests()
    await tests.run_all_tests()
    tests.print_test_summary()


if __name__ == "__main__":
    asyncio.run(main())