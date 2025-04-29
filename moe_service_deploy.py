"""
MOE Service Deployment Script
-----------------------------
This script handles the deployment setup for the MOE service component.
It should be run on the server that will host the MOE service.
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def check_prerequisites():
    """Check if all prerequisites are met for deployment"""
    print_header("CHECKING PREREQUISITES")
    
    # Check if Python 3.8+ is installed
    print("\nChecking Python version...")
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print(f"✅ Python {python_version.major}.{python_version.minor} is installed")
        python_ok = True
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor} is installed, but 3.8+ is required")
        python_ok = False
    
    # Check if pip is installed
    print("\nChecking pip installation...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
        print("✅ pip is installed")
        pip_ok = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pip is not installed or not working properly")
        pip_ok = False
    
    # Check if required files exist
    print("\nChecking required MOE service files...")
    required_files = [
        "fastapi_moe_example.py",
        "moe_gating_mechanism.py",
        "byt5_integration.py",
        "longformer_integration.py",
        "moe_optimizations.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
            print(f"❌ {file} is missing")
        else:
            print(f"✅ {file} is present")
    
    files_ok = len(missing_files) == 0
    
    # Overall prerequisites check
    prerequisites_met = python_ok and pip_ok and files_ok
    
    print("\nPrerequisites check:", "✅ PASSED" if prerequisites_met else "❌ FAILED")
    
    if not prerequisites_met:
        print("\n⚠️ Some prerequisites are not met. Please fix the issues before proceeding.")
        if missing_files:
            print(f"Missing files: {', '.join(missing_files)}")
    
    return prerequisites_met


def install_dependencies():
    """Install required dependencies for the MOE service"""
    print_header("INSTALLING DEPENDENCIES")
    
    try:
        print("Installing dependencies from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        
        # Install additional deployment dependencies
        print("\nInstalling deployment dependencies...")
        deploy_deps = ["gunicorn", "uvicorn", "python-dotenv"]
        subprocess.run([sys.executable, "-m", "pip", "install"] + deploy_deps, check=True)
        print("✅ Deployment dependencies installed successfully")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_service_files():
    """Create necessary service files for production deployment"""
    print_header("CREATING SERVICE FILES")
    
    # Create .env file for the MOE service
    print("Creating .env file for the MOE service...")
    env_content = """# MOE Service Environment Variables
PORT=8000
HOST=0.0.0.0
WORKERS=1
LOG_LEVEL=info
TIMEOUT=120
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    print("✅ Created .env file")
    
    # Create systemd service file
    print("Creating systemd service file...")
    service_content = """[Unit]
Description=MOE AI Service
After=network.target

[Service]
User=USERNAME
WorkingDirectory=/path/to/moe/service
Environment="PATH=/path/to/moe/service/venv/bin"
ExecStart=/path/to/moe/service/venv/bin/gunicorn fastapi_moe_example:app -k uvicorn.workers.UvicornWorker -w 1 --bind 0.0.0.0:8000 --timeout 120
Restart=always
RestartSec=5
SyslogIdentifier=moe-service

[Install]
WantedBy=multi-user.target
"""
    
    with open("moe-service.service", "w") as f:
        f.write(service_content)
    print("✅ Created systemd service file template (moe-service.service)")
    print("⚠️ You need to customize this file with your actual paths before installing")
    
    # Create start script
    print("Creating start script...")
    start_script = """#!/bin/bash
# Start the MOE service in production mode

# Load environment variables
set -a
source .env
set +a

# Start the service with gunicorn
exec gunicorn fastapi_moe_example:app -k uvicorn.workers.UvicornWorker -w $WORKERS --bind $HOST:$PORT --timeout $TIMEOUT --log-level $LOG_LEVEL
"""
    
    with open("start-moe-service.sh", "w") as f:
        f.write(start_script)
    
    # Make the script executable
    os.chmod("start-moe-service.sh", 0o755)
    print("✅ Created start script (start-moe-service.sh)")
    
    return True


def create_nginx_config():
    """Create Nginx configuration for reverse proxy"""
    print_header("CREATING NGINX CONFIGURATION")
    
    nginx_conf = """server {
    listen 80;
    server_name moe-service.yourdomain.com;  # Replace with your actual domain
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
    
    with open("moe-service-nginx.conf", "w") as f:
        f.write(nginx_conf)
    
    print("✅ Created Nginx configuration (moe-service-nginx.conf)")
    print("⚠️ You need to customize this file with your actual domain before installing")
    print("📋 Installation instructions:")
    print("   1. Copy to /etc/nginx/sites-available/")
    print("   2. Create symlink in /etc/nginx/sites-enabled/")
    print("   3. Test configuration: sudo nginx -t")
    print("   4. Reload Nginx: sudo systemctl reload nginx")
    
    return True


def test_service():
    """Test the MOE service locally"""
    print_header("TESTING MOE SERVICE")
    
    print("Starting MOE service for testing...")
    
    # Start the service in a subprocess
    process = subprocess.Popen([sys.executable, "fastapi_moe_example.py"], 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    
    # Wait a bit for the service to start
    import time
    time.sleep(5)
    
    # Check if the process is still running
    if process.poll() is None:
        print("✅ MOE service started successfully")
        
        # Test health endpoint
        try:
            import requests
            print("\nTesting health endpoint...")
            response = requests.get("http://localhost:8000/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed: {json.dumps(health_data, indent=2)}")
                
                # Test a simple processing request
                print("\nTesting processing endpoint...")
                test_data = {
                    "text": "This is a test message for the MOE service.",
                    "task": "process"
                }
                
                response = requests.post("http://localhost:8000/process/sync", 
                                        json=test_data, 
                                        timeout=30)
                
                if response.status_code == 200:
                    process_data = response.json()
                    print(f"✅ Processing test passed")
                    print(f"   Expert used: {process_data.get('expert_used')}")
                    print(f"   Processing time: {process_data.get('processing_time')} seconds")
                    test_success = True
                else:
                    print(f"❌ Processing test failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    test_success = False
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print(f"   Response: {response.text}")
                test_success = False
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            test_success = False
    else:
        stdout, stderr = process.communicate()
        print("❌ MOE service failed to start")
        print(f"Error output: {stderr.decode('utf-8')}")
        test_success = False
    
    # Clean up - terminate the process if it's still running
    if process.poll() is None:
        process.terminate()
        process.wait()
    
    return test_success


def print_deployment_instructions():
    """Print instructions for manual steps needed"""
    print_header("DEPLOYMENT INSTRUCTIONS")
    
    print("""
To complete the MOE service deployment:

1. Configure your DNS to point to your server
2. Set up SSL/TLS with Let's Encrypt:
   ```
   sudo certbot --nginx -d moe-service.yourdomain.com
   ```

3. Update the systemd service file with correct paths:
   ```
   sudo nano moe-service.service
   # Update paths and username
   sudo cp moe-service.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable moe-service
   sudo systemctl start moe-service
   ```

4. Test the deployed service:
   ```
   curl https://moe-service.yourdomain.com/health
   ```

5. Update your NextJS app's .env with the correct URL:
   MOE_API_URL=https://moe-service.yourdomain.com

6. Deploy your NextJS app to Vercel with:
   ```
   vercel
   ```
   
7. Set environment variables in the Vercel dashboard.

8. Once deployed, configure your custom domain in Vercel.
""")


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy MOE service")
    parser.add_argument("--skip-prereq", action="store_true", help="Skip prerequisites check")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--skip-test", action="store_true", help="Skip service testing")
    
    args = parser.parse_args()
    
    print_header("MOE SERVICE DEPLOYMENT")
    
    # Check prerequisites
    if not args.skip_prereq:
        prereq_ok = check_prerequisites()
        if not prereq_ok:
            choice = input("Prerequisites check failed. Continue anyway? (y/n): ")
            if choice.lower() != 'y':
                print("Deployment aborted.")
                return
    
    # Install dependencies
    if not args.skip_deps:
        deps_ok = install_dependencies()
        if not deps_ok:
            print("Failed to install dependencies. Deployment aborted.")
            return
    
    # Create service files
    files_ok = create_service_files()
    if not files_ok:
        print("Failed to create service files. Deployment aborted.")
        return
    
    # Create Nginx config
    nginx_ok = create_nginx_config()
    if not nginx_ok:
        print("Failed to create Nginx configuration. Deployment aborted.")
        return
    
    # Test service
    if not args.skip_test:
        test_ok = test_service()
        if not test_ok:
            choice = input("Service test failed. Continue anyway? (y/n): ")
            if choice.lower() != 'y':
                print("Deployment aborted.")
                return
    
    # Print deployment instructions
    print_deployment_instructions()
    
    print("\n✅ Deployment setup completed successfully!")
    print("Follow the instructions above to complete the manual deployment steps.")


if __name__ == "__main__":
    main()