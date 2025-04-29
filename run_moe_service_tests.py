"""
MOE Service Direct Testing
-------------------------
This script tests the Python MOE service directly using the testing examples.
"""

import time
import json
import sys
from typing import Dict, Any, List, Optional
import requests

# Import test functions from moe_testing_examples.py
from moe_testing_examples import (
    test_health_endpoint,
    test_process_endpoint,
    test_process_long_text,
    test_process_binary_data,
    test_embedding_task,
    test_with_options,
    test_sync_endpoint
)

# Configuration
MOE_API_URL = "http://localhost:8000"

def verify_expert_routing(base_url: str = MOE_API_URL) -> Dict[str, Any]:
    """
    Verify that requests are correctly routed to the appropriate expert models.
    
    Args:
        base_url: Base URL of the MOE API
        
    Returns:
        Dictionary containing test results
    """
    print("\nVerifying expert routing...")
    
    # Test cases designed to trigger different experts
    test_cases = [
        {
            "name": "Short text (likely ByT5)",
            "text": "This is a short test message that should be routed to the ByT5 expert.",
            "expected_expert": "byt5"
        },
        {
            "name": "Long text (likely Longformer)",
            "text": "This is a much longer text that should be routed to the Longformer expert. " * 50,
            "expected_expert": "longformer"
        },
        {
            "name": "Binary data (likely ByT5)",
            "text": f"Binary-like data with special chars: {chr(1)}{chr(2)}{chr(3)}{chr(4)}",
            "expected_expert": "byt5"
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        name = test_case["name"]
        text = test_case["text"]
        expected = test_case["expected_expert"]
        
        print(f"  Testing: {name}")
        
        url = f"{base_url}/process/sync"
        
        # Prepare input data
        input_data = {
            "text": text,
            "task": "process",
            "options": {}
        }
        
        try:
            # Send request
            response = requests.post(url, json=input_data, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check if routed to expected expert
            actual_expert = data.get("expert_used", "unknown")
            confidence = data.get("confidence", 0)
            
            results[name] = {
                "expected_expert": expected,
                "actual_expert": actual_expert,
                "routed_correctly": expected == actual_expert,
                "confidence": confidence,
                "processing_time": data.get("processing_time", 0)
            }
            
            print(f"    Result: Routed to {actual_expert} with confidence {confidence:.4f}")
            
        except requests.RequestException as e:
            results[name] = {
                "error": str(e),
                "routed_correctly": False
            }
            print(f"    Error: {e}")
    
    return results

def test_specific_expert(expert: str, base_url: str = MOE_API_URL) -> Dict[str, Any]:
    """
    Test a specific expert model explicitly.
    
    Args:
        expert: The expert model to test ("byt5" or "longformer")
        base_url: Base URL of the MOE API
        
    Returns:
        Dictionary containing test results
    """
    print(f"\nTesting specific expert: {expert}")
    
    url = f"{base_url}/process/sync"
    
    # Prepare input data
    input_data = {
        "text": f"This is a test specifically for the {expert} expert model.",
        "task": "process",
        "options": {"force_expert": expert}  # Force specific expert usage
    }
    
    try:
        # Send request
        response = requests.post(url, json=input_data, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check if correct expert was used
        actual_expert = data.get("expert_used", "unknown")
        
        result = {
            "requested_expert": expert,
            "actual_expert": actual_expert,
            "used_correct_expert": expert == actual_expert,
            "processing_time": data.get("processing_time", 0),
            "result": data.get("result", "")[:100] + "..." if data.get("result") else ""
        }
        
        print(f"  Result: Used {actual_expert} expert")
        return result
        
    except requests.RequestException as e:
        result = {
            "requested_expert": expert,
            "error": str(e),
            "used_correct_expert": False
        }
        print(f"  Error: {e}")
        return result

def verify_fallback_mechanism():
    """
    Verify that the fallback mechanism works properly.
    This requires manual intervention to disable the MOE service.
    
    Returns:
        Dictionary containing test results
    """
    print("\nVerifying fallback mechanism...")
    print("This test requires manual intervention.")
    print("Please stop the MOE service temporarily (Ctrl+C in the MOE service terminal)")
    
    choice = input("Do you want to continue with the fallback test? (y/n): ")
    if choice.lower() != 'y':
        print("Skipping fallback test.")
        return {"status": "skipped"}
    
    input("Press Enter when the MOE service is stopped...")
    
    # Verify service is actually down
    try:
        response = requests.get(f"{MOE_API_URL}/health", timeout=2)
        if response.status_code == 200:
            print("The MOE service is still running! Fallback test cannot be performed.")
            print("Please stop the service and try again.")
            return {
                "status": "error",
                "message": "MOE service still running"
            }
    except requests.RequestException:
        # This is expected - service should be down
        pass
    
    print("MOE service confirmed down. Now testing NextJS fallback...")
    print("The NextJS application should automatically use the fallback provider.")
    print("Check the NextJS application logs for 'MOE API unavailable, falling back to default provider'")
    
    # Wait for verification
    input("After checking the logs, press Enter to continue...")
    print("Please restart the MOE service now.")
    input("Press Enter when the MOE service is restarted...")
    
    # Verify service is back up
    try:
        response = requests.get(f"{MOE_API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("MOE service successfully restarted.")
            return {
                "status": "completed",
                "message": "Fallback test completed, manually verified"
            }
        else:
            print("MOE service health check failed after restart.")
            return {
                "status": "warning",
                "message": "MOE service health check failed after restart"
            }
    except requests.RequestException as e:
        print(f"Error checking MOE service health after restart: {e}")
        return {
            "status": "error",
            "message": f"Failed to verify MOE service restart: {e}"
        }

def run_comprehensive_tests(base_url: str = MOE_API_URL):
    """
    Run comprehensive tests on the MOE service.
    Includes original tests from moe_testing_examples.py and additional tests.
    
    Args:
        base_url: Base URL of the MOE API
    """
    all_results = {}
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE MOE SERVICE TESTS")
    print("=" * 60)
    
    # 1. Basic health check
    print("\n1. Testing MOE service health...")
    try:
        health_result = test_health_endpoint(base_url)
        all_results["health"] = health_result
        print(f"  Health status: {json.dumps(health_result, indent=2)}")
        
        if health_result.get("status") != "healthy":
            print("MOE service is not healthy! Please check if it's running properly.")
            print("Aborting further tests.")
            return all_results
    except Exception as e:
        print(f"  Error checking health: {e}")
        print("MOE service health check failed! Please ensure the service is running.")
        print("Aborting further tests.")
        all_results["health"] = {"error": str(e)}
        return all_results
    
    # 2. Basic processing test
    print("\n2. Testing basic processing...")
    try:
        process_result = test_process_endpoint(base_url)
        all_results["basic_processing"] = {
            "expert_used": process_result.get("expert_used"),
            "confidence": process_result.get("confidence"),
            "processing_time": process_result.get("processing_time")
        }
        print(f"  Expert used: {process_result.get('expert_used')}")
        print(f"  Processing time: {process_result.get('processing_time')} seconds")
    except Exception as e:
        print(f"  Error in basic processing: {e}")
        all_results["basic_processing"] = {"error": str(e)}
    
    # 3. Long text processing
    print("\n3. Testing long text processing...")
    try:
        long_result = test_process_long_text(base_url)
        all_results["long_text"] = {
            "expert_used": long_result.get("expert_used"),
            "confidence": long_result.get("confidence"),
            "processing_time": long_result.get("processing_time")
        }
        print(f"  Expert used: {long_result.get('expert_used')}")
        print(f"  Processing time: {long_result.get('processing_time')} seconds")
    except Exception as e:
        print(f"  Error in long text processing: {e}")
        all_results["long_text"] = {"error": str(e)}
    
    # 4. Binary data processing
    print("\n4. Testing binary data processing...")
    try:
        binary_result = test_process_binary_data(base_url)
        all_results["binary_data"] = {
            "expert_used": binary_result.get("expert_used"),
            "confidence": binary_result.get("confidence"),
            "processing_time": binary_result.get("processing_time")
        }
        print(f"  Expert used: {binary_result.get('expert_used')}")
        print(f"  Processing time: {binary_result.get('processing_time')} seconds")
    except Exception as e:
        print(f"  Error in binary data processing: {e}")
        all_results["binary_data"] = {"error": str(e)}
    
    # 5. Embedding task
    print("\n5. Testing embedding task...")
    try:
        embedding_result = test_embedding_task(base_url)
        all_results["embedding"] = {
            "expert_used": embedding_result.get("expert_used"),
            "processing_time": embedding_result.get("processing_time", 0)
        }
        print(f"  Expert used: {embedding_result.get('expert_used')}")
    except Exception as e:
        print(f"  Error in embedding task: {e}")
        all_results["embedding"] = {"error": str(e)}
    
    # 6. Testing with options
    print("\n6. Testing with options...")
    try:
        options_result = test_with_options(base_url)
        all_results["with_options"] = {
            "expert_used": options_result.get("expert_used"),
            "result": options_result.get("result", "")[:50] + "..." if options_result.get("result") else ""
        }
        print(f"  Expert used: {options_result.get('expert_used')}")
        print(f"  Result: {options_result.get('result', '')[:50]}...")
    except Exception as e:
        print(f"  Error in testing with options: {e}")
        all_results["with_options"] = {"error": str(e)}
    
    # 7. Sync endpoint
    print("\n7. Testing sync endpoint...")
    try:
        sync_result = test_sync_endpoint(base_url)
        all_results["sync_endpoint"] = {
            "expert_used": sync_result.get("expert_used"),
            "processing_time": sync_result.get("processing_time")
        }
        print(f"  Expert used: {sync_result.get('expert_used')}")
        print(f"  Processing time: {sync_result.get('processing_time')} seconds")
    except Exception as e:
        print(f"  Error in sync endpoint test: {e}")
        all_results["sync_endpoint"] = {"error": str(e)}
    
    # 8. Expert routing verification
    routing_results = verify_expert_routing(base_url)
    all_results["expert_routing"] = routing_results
    
    # 9. Specific expert tests
    byt5_result = test_specific_expert("byt5", base_url)
    longformer_result = test_specific_expert("longformer", base_url)
    all_results["specific_experts"] = {
        "byt5": byt5_result,
        "longformer": longformer_result
    }
    
    # 10. Fallback mechanism (manual)
    choice = input("\nDo you want to test the fallback mechanism? (y/n): ")
    if choice.lower() == 'y':
        fallback_result = verify_fallback_mechanism()
        all_results["fallback"] = fallback_result
    else:
        print("Skipping fallback test.")
        all_results["fallback"] = {"status": "skipped"}
    
    return all_results

def print_test_summary(results):
    """
    Print a summary of all test results
    
    Args:
        results: Dictionary of test results
    """
    print("\n" + "=" * 60)
    print("MOE SERVICE TEST SUMMARY")
    print("=" * 60)
    
    # Check health
    health_status = "Healthy" if results.get("health", {}).get("status") == "healthy" else "Unhealthy"
    print(f"\nService Health: {health_status}")
    
    # Processing tests
    print("\nProcessing Tests:")
    processing_tests = ["basic_processing", "long_text", "binary_data", "embedding", "with_options", "sync_endpoint"]
    for test in processing_tests:
        result = results.get(test, {})
        if "error" in result:
            print(f"  ❌ {test}: Error - {result['error']}")
        else:
            print(f"  ✅ {test}: Expert used: {result.get('expert_used', 'N/A')}")
    
    # Expert routing
    print("\nExpert Routing:")
    routing_results = results.get("expert_routing", {})
    correct_routing = sum(1 for r in routing_results.values() if r.get("routed_correctly", False))
    total_routing = len(routing_results)
    print(f"  Correctly routed: {correct_routing}/{total_routing}")
    
    for name, result in routing_results.items():
        if "error" in result:
            print(f"  ❌ {name}: Error - {result['error']}")
        else:
            status = "✅" if result.get("routed_correctly", False) else "❌"
            print(f"  {status} {name}: Expected {result.get('expected_expert')}, got {result.get('actual_expert')}")
    
    # Specific experts
    print("\nSpecific Expert Tests:")
    specific_results = results.get("specific_experts", {})
    for expert, result in specific_results.items():
        if "error" in result:
            print(f"  ❌ {expert}: Error - {result['error']}")
        else:
            status = "✅" if result.get("used_correct_expert", False) else "❌"
            print(f"  {status} {expert}: Used correct expert: {result.get('used_correct_expert', False)}")
    
    # Fallback mechanism
    fallback = results.get("fallback", {})
    fallback_status = fallback.get("status", "not tested")
    print(f"\nFallback Mechanism: {fallback_status}")
    if "message" in fallback:
        print(f"  Note: {fallback['message']}")
    
    # Overall summary
    print("\nOVERALL STATUS:")
    
    # Count successful tests
    health_ok = results.get("health", {}).get("status") == "healthy"
    processing_ok = all("error" not in results.get(test, {}) for test in processing_tests)
    routing_ok = correct_routing == total_routing
    experts_ok = all(r.get("used_correct_expert", False) for r in specific_results.values())
    
    if health_ok and processing_ok and routing_ok and experts_ok:
        print("✅ MOE SERVICE IS FUNCTIONING PROPERLY!")
    else:
        print("⚠️ MOE SERVICE HAS ISSUES THAT NEED ATTENTION")
        
        if not health_ok:
            print("  ❌ Health check failed")
        if not processing_ok:
            print("  ❌ Some processing tests failed")
        if not routing_ok:
            print("  ❌ Expert routing has issues")
        if not experts_ok:
            print("  ❌ Specific expert tests failed")

if __name__ == "__main__":
    # Run all tests
    results = run_comprehensive_tests()
    
    # Print summary
    print_test_summary(results)
    
    print("\nTesting completed!")