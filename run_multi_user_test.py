"""
Quick Multi-User Test Runner

Running this script will automatically start the Locust test interface
"""

import subprocess
import sys
import webbrowser
import time
import os

def check_locust():
    """Check if Locust is installed"""
    try:
        import locust
        print("✓ Locust is installed")
        return True
    except ImportError:
        print("✗ Locust is not installed")
        print("Please run: pip install locust")
        return False

def check_django_server():
    """Check if Django server is running"""
    import urllib.request
    try:
        response = urllib.request.urlopen('http://localhost:8000', timeout=5)
        print("✓ Django server is running")
        return True
    except:
        print("✗ Django server is not running")
        print("Please run in another terminal: python manage.py runserver")
        return False

def main():
    print("="*50)
    print("Multi-User Concurrent Test (20-100 Users)")
    print("="*50)
    
    # Check dependencies
    if not check_locust():
        return
    
    # Check Django server
    if not check_django_server():
        response = input("Continue to start test? (y/n): ")
        if response.lower() != 'y':
            return
    
    print("\nStarting Locust test interface...")
    print("Test configuration recommendations:")
    print("- Number of users: 20-100")
    print("- Spawn rate: 5-10 users/second")
    print("- Test duration: 5-10 minutes")
    
    try:
        # Start Locust
        print("\nStarting Locust...")
        time.sleep(2)
        
        # Auto open browser
        webbrowser.open('http://localhost:8089')
        
        # Run Locust command
        subprocess.run([
            "locust", 
            "-f", "multi_user_test.py", 
            "--host=http://localhost:8000"
        ])
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except FileNotFoundError:
        print("Error: locust command not found")
        print("Please ensure locust is installed: pip install locust")
    except Exception as e:
        print(f"Error starting test: {str(e)}")

if __name__ == "__main__":
    main()