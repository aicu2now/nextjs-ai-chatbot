"""
NextJS Chat Application MOE Integration Test
-------------------------------------------
This script tests the Mixture of Experts (MOE) integration in the NextJS chat application.
"""

import requests
import json
import time
from typing import Dict, Any, List, Optional

# Configuration
MOE_API_URL = "http://localhost:8000"
NEXTJS_API_URL = "http://localhost:3000/api"

def test_moe_health() -> Dict[str, Any]:
    """
    Test the health of the MOE service.
    
    Returns:
        Health status response
    """
    url = f"{MOE_API_URL}/health"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"MOE Health Check Error: {e}")
        return {"status": "unavailable", "error": str(e)}

def test_nextjs_chat_with_moe(model_id: str, message: str) -> Dict[str, Any]:
    """
    Test the NextJS chat API with a specific MOE model.
    
    Args:
        model_id: The MOE model ID to use (e.g., moe-expert-byt5)
        message: The message to send
        
    Returns:
        Response from the chat API
    """
    url = f"{NEXTJS_API_URL}/chat"
    
    payload = {
        "id": f"test-chat-{int(time.time())}",
        "message": {
            "id": f"msg-{int(time.time())}",
            "role": "user",
            "content": message
        },
        "selectedChatModel": model_id
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return {
            "status": "success",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            # For streaming responses, we won't return content
            "is_streaming": "text/event-stream" in response.headers.get("content-type", "")
        }
    except requests.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "status_code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None
        }

def test_fallback_mechanism() -> Dict[str, Any]:
    """
    Test the fallback mechanism by temporarily making the MOE service unavailable.
    
    Returns:
        Test results
    """
    print("Testing fallback mechanism - Note: This test assumes MOE service can be manipulated")
    print("Please manually stop the MOE service or block port 8000 temporarily")
    
    # Wait for user confirmation
    input("Press Enter when the MOE service is unavailable to continue the test...")
    
    # Check if MOE is actually unavailable
    health = test_moe_health()
    if health.get("status") == "healthy":
        return {
            "status": "error", 
            "message": "MOE service is still available. Fallback test cannot be completed."
        }
    
    # Test with each MOE model to verify fallback
    models = ["moe-expert-byt5", "moe-expert-longformer", "moe-auto"]
    results = {}
    
    for model in models:
        result = test_nextjs_chat_with_moe(model, f"Test fallback for {model}")
        results[model] = result
    
    # Prompt to restart MOE service
    print("Fallback tests completed. Please restart the MOE service.")
    input("Press Enter when the MOE service is available again...")
    
    return {
        "status": "completed",
        "results": results
    }

def run_all_tests():
    """
    Run all MOE integration tests.
    """
    print("Starting MOE Integration Tests for NextJS Chat Application")
    print("=" * 60)
    
    # 1. Test MOE service health
    print("\n1. Testing MOE Service Health...")
    health = test_moe_health()
    print(f"Health status: {json.dumps(health, indent=2)}")
    
    if health.get("status") != "healthy":
        print("MOE service is not healthy! Please start the MOE service before continuing.")
        choice = input("Do you want to continue testing anyway? (y/n): ")
        if choice.lower() != 'y':
            print("Tests aborted.")
            return
    
    # 2. Test each MOE model
    print("\n2. Testing Chat API with MOE models...")
    models = ["moe-expert-byt5", "moe-expert-longformer", "moe-auto"]
    
    for model in models:
        print(f"\nTesting {model}...")
        result = test_nextjs_chat_with_moe(model, f"This is a test message for {model}")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if result.get("status") == "success" and result.get("is_streaming"):
            print(f"✓ {model} properly returns a streaming response")
        else:
            print(f"✗ {model} failed to return a proper streaming response")
    
    # 3. Test error handling with a very long message
    print("\n3. Testing error handling with a very long message...")
    long_message = "Testing with a very long message. " * 500  # Very long message
    result = test_nextjs_chat_with_moe("moe-auto", long_message)
    print(f"Long message result: {json.dumps(result, indent=2)}")
    
    # 4. Test fallback mechanism (requires manual intervention)
    print("\n4. Testing fallback mechanism...")
    choice = input("Do you want to test the fallback mechanism? (This requires manual intervention) (y/n): ")
    if choice.lower() == 'y':
        fallback_result = test_fallback_mechanism()
        print(f"Fallback test results: {json.dumps(fallback_result, indent=2)}")
    else:
        print("Skipping fallback test.")
    
    print("\n5. Testing invalid input handling...")
    invalid_payload = {
        "invalid": "payload"
    }
    try:
        response = requests.post(f"{NEXTJS_API_URL}/chat", json=invalid_payload, timeout=10)
        print(f"Invalid payload response: Status {response.status_code}")
        print(f"Response body: {response.text}")
    except requests.RequestException as e:
        print(f"Error with invalid payload: {e}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    run_all_tests()