"""
Main MOE Integration Test Script
-------------------------------
This script coordinates all MOE integration tests and provides a comprehensive report.
"""

import os
import sys
import time
import json
import subprocess
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def check_prerequisites():
    """Check if all prerequisites are met for running the tests"""
    print_header("CHECKING PREREQUISITES")
    
    # Check if the Python MOE service is running
    print("\nChecking if Python MOE service is running...")
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ MOE service is running and healthy")
                moe_service_running = True
            else:
                print("⚠️ MOE service is running but reports unhealthy status")
                moe_service_running = True
        else:
            print("❌ MOE service returned error status code:", response.status_code)
            moe_service_running = False
    except Exception as e:
        print(f"❌ MOE service check failed: {e}")
        print("   Make sure the MOE service is running on http://localhost:8000")
        moe_service_running = False
    
    # Check if NextJS app is running
    print("\nChecking if NextJS app is running...")
    try:
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ NextJS app is running")
            nextjs_running = True
        else:
            print("❌ NextJS app health check returned error status code:", response.status_code)
            nextjs_running = False
    except Exception as e:
        print(f"❌ NextJS app check failed: {e}")
        print("   Make sure the NextJS app is running on http://localhost:3000")
        nextjs_running = False
    
    # Check if required Python packages are installed
    print("\nChecking required Python packages...")
    required_packages = ["requests", "aiohttp", "asyncio"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is not installed")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("   Install them with: pip install " + " ".join(missing_packages))
    
    # Overall prerequisites status
    prerequisites_met = moe_service_running and nextjs_running and not missing_packages
    
    print("\nPrerequisites check result:", "✅ PASSED" if prerequisites_met else "❌ FAILED")
    return prerequisites_met


def run_test_script(script_path, description):
    """Run a test script and return its success status"""
    print_header(f"RUNNING {description}")
    print(f"Executing: {script_path}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            text=True,
            capture_output=True
        )
        success = True
        output = result.stdout
        error = result.stderr
    except subprocess.CalledProcessError as e:
        success = False
        output = e.stdout
        error = e.stderr
    
    duration = time.time() - start_time
    
    print(f"\nTest completed in {duration:.2f} seconds")
    print(f"Status: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if output:
        print("\nOutput:")
        print(output)
    
    if error:
        print("\nErrors:")
        print(error)
    
    return {
        "success": success,
        "duration": duration,
        "output": output,
        "error": error
    }


def save_test_report(results, output_dir="./test-reports"):
    """Save the test results to a JSON file"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create report filename
    filename = f"{output_dir}/moe_test_report_{timestamp}.json"
    
    # Sanitize results for JSON serialization
    report = {
        "timestamp": timestamp,
        "overall_success": all(test["success"] for test in results.values()),
        "tests": {
            name: {
                "success": test["success"],
                "duration": test["duration"],
                "output_excerpt": test["output"][:500] + "..." if len(test["output"]) > 500 else test["output"],
                "error_excerpt": test["error"][:500] + "..." if len(test["error"]) > 500 else test["error"]
            }
            for name, test in results.items()
        }
    }
    
    # Save to file
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nTest report saved to: {filename}")
    return filename


def main():
    """Main function to run all MOE integration tests"""
    parser = argparse.ArgumentParser(description="Run MOE integration tests")
    parser.add_argument("--skip-prereq", action="store_true", help="Skip prerequisites check")
    parser.add_argument("--skip-service", action="store_true", help="Skip MOE service tests")
    parser.add_argument("--skip-nextjs", action="store_true", help="Skip NextJS integration tests")
    parser.add_argument("--skip-edge", action="store_true", help="Skip edge case tests")
    parser.add_argument("--report-dir", default="./test-reports", help="Directory to save test reports")
    
    args = parser.parse_args()
    
    print_header("MOE INTEGRATION TEST SUITE")
    print("Starting test suite at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Check prerequisites
    if not args.skip_prereq:
        prerequisites_met = check_prerequisites()
        if not prerequisites_met:
            print("\n⚠️ Prerequisites check failed.")
            choice = input("Do you want to continue anyway? (y/n): ")
            if choice.lower() != 'y':
                print("Aborting tests.")
                return
    
    # Run tests
    test_results = {}
    
    # 1. Run MOE Service Tests
    if not args.skip_service:
        test_results["moe_service"] = run_test_script(
            "run_moe_service_tests.py",
            "MOE SERVICE TESTS"
        )
    
    # 2. Run NextJS Integration Tests
    if not args.skip_nextjs:
        test_results["nextjs_integration"] = run_test_script(
            "nextjs_moe_integration_test.py",
            "NEXTJS INTEGRATION TESTS"
        )
    
    # 3. Run Edge Case Tests
    if not args.skip_edge:
        test_results["edge_cases"] = run_test_script(
            "moe_edge_case_tests.py",
            "EDGE CASE TESTS"
        )
    
    # Print summary
    print_header("TEST SUMMARY")
    
    all_tests_passed = all(test["success"] for test in test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{test_name}: {status} ({result['duration']:.2f}s)")
    
    print("\nOVERALL STATUS:", "✅ PASSED" if all_tests_passed else "❌ FAILED")
    
    # Save test report
    report_file = save_test_report(test_results, args.report_dir)
    
    # Final message
    if all_tests_passed:
        print("\n✅ MOE integration appears to be working correctly!")
    else:
        print("\n⚠️ Some tests failed. Please review the test outputs and fix the issues.")
    
    print("\nTest suite completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    

if __name__ == "__main__":
    main()