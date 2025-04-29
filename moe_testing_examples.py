"""
MOE Framework Testing Examples
-----------------------------
This module provides simple testing examples for the MOE framework API.
"""

import requests
import json
import time
from typing import Dict, Any


def test_health_endpoint(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Test the health endpoint of the MOE API.
    
    Args:
        base_url: Base URL of the MOE API
        
    Returns:
        Health status response
    """
    url = f"{base_url}/health"
    response = requests.get(url)
    response.raise_for_status()
    
    return response.json()


def test_process_endpoint(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Test the process endpoint of the MOE API with a simple text input.
    
    Args:
        base_url: Base URL of the MOE API
        
    Returns:
        Processing response
    """
    url = f"{base_url}/process"
    
    # Prepare input data
    input_data = {
        "text": "This is a test of the MOE framework API with a simple text input.",
        "task": "process",
        "options": {}
    }
    
    # Send request
    response = requests.post(url, json=input_data)
    response.raise_for_status()
    
    return response.json()


def test_process_long_text(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Test the process endpoint of the MOE API with a long text input.
    
    Args:
        base_url: Base URL of the MOE API
        
    Returns:
        Processing response
    """
    url = f"{base_url}/process"
    
    # Prepare input data with long text
    long_text = "This is a test of the MOE framework API with a long text input. " * 100
    input_data = {
        "text": long_text,
        "task": "process",
        "options": {}
    }
    
    # Send request
    response = requests.post(url, json=input_data)
    response.raise_for_status()
    
    return response.json()


def test_process_binary_data(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Test the process endpoint of the MOE API with binary data.
    
    Args:
        base_url: Base URL of the MOE API
        
    Returns:
        Processing response
    """
    url = f"{base_url}/process"
    
    # Prepare input data with binary content
    binary_text = "Binary data: " + "".join([chr(i) for i in range(0, 32)])
    input_data = {
        "text": binary_text,
        "task": "process",
        "options": {}
    }
    
    # Send request
    response = requests.post(url, json=input_data)
    response.raise_for_status()
    
    return response.json()


def test_embedding_task(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Test the process endpoint of the MOE API with embedding task.
    
    Args:
        base_url: Base URL of the MOE API
        
    Returns:
        Processing response
    """
    url = f"{base_url}/process"
    
    # Prepare input data for embedding
    input_data = {
        "text": "This is a test of the MOE framework API with embedding task.",
        "task": "embed",
        "options": {}
    }
    
    # Send request
    response = requests.post(url, json=input_data)
    response.raise_for_status()
    
    return response.json()


def test_with_options(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Test the process endpoint of the MOE API with additional options.
    
    Args:
        base_url: Base URL of the MOE API
        
    Returns:
        Processing response
    """
    url = f"{base_url}/process"
    
    # Prepare input data with options
    input_data = {
        "text": "This is a test of the MOE framework API with additional options.",
        "task": "process",
        "options": {
            "truncate_length": 20,
            "to_uppercase": True
        }
    }
    
    # Send request
    response = requests.post(url, json=input_data)
    response.raise_for_status()
    
    return response.json()


def test_sync_endpoint(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Test the synchronous process endpoint of the MOE API.
    
    Args:
        base_url: Base URL of the MOE API
        
    Returns:
        Processing response
    """
    url = f"{base_url}/process/sync"
    
    # Prepare input data
    input_data = {
        "text": "This is a test of the MOE framework API with synchronous processing.",
        "task": "process",
        "options": {}
    }
    
    # Send request
    response = requests.post(url, json=input_data)
    response.raise_for_status()
    
    return response.json()


def run_all_tests(base_url: str = "http://localhost:8000") -> None:
    """
    Run all tests for the MOE API.
    
    Args:
        base_url: Base URL of the MOE API
    """
    print("Running MOE API tests...")
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    health_response = test_health_endpoint(base_url)
    print(f"Health status: {json.dumps(health_response, indent=2)}")
    
    # Test process endpoint with simple text
    print("\n2. Testing process endpoint with simple text...")
    process_response = test_process_endpoint(base_url)
    print(f"Expert used: {process_response['expert_used']}")
    print(f"Confidence: {process_response['confidence']}")
    print(f"Processing time: {process_response['processing_time']} seconds")
    print(f"Result: {process_response['result'][:100]}...")
    
    # Test process endpoint with long text
    print("\n3. Testing process endpoint with long text...")
    long_response = test_process_long_text(base_url)
    print(f"Expert used: {long_response['expert_used']}")
    print(f"Confidence: {long_response['confidence']}")
    print(f"Processing time: {long_response['processing_time']} seconds")
    
    # Test process endpoint with binary data
    print("\n4. Testing process endpoint with binary data...")
    binary_response = test_process_binary_data(base_url)
    print(f"Expert used: {binary_response['expert_used']}")
    print(f"Confidence: {binary_response['confidence']}")
    print(f"Processing time: {binary_response['processing_time']} seconds")
    
    # Test embedding task
    print("\n5. Testing embedding task...")
    embedding_response = test_embedding_task(base_url)
    print(f"Expert used: {embedding_response['expert_used']}")
    print(f"Result: {embedding_response['result']}")
    
    # Test with options
    print("\n6. Testing with options...")
    options_response = test_with_options(base_url)
    print(f"Expert used: {options_response['expert_used']}")
    print(f"Result: {options_response['result']}")
    
    # Test sync endpoint
    print("\n7. Testing sync endpoint...")
    sync_response = test_sync_endpoint(base_url)
    print(f"Expert used: {sync_response['expert_used']}")
    print(f"Processing time: {sync_response['processing_time']} seconds")
    
    print("\nAll tests completed successfully!")


def main():
    """
    Main function to run the tests.
    """
    # Set base URL
    base_url = "http://localhost:8000"
    
    # Run all tests
    run_all_tests(base_url)


if __name__ == "__main__":
    main()
