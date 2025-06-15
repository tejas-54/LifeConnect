import os
import sys
import subprocess
import time

def start_backend():
    """Start the complete backend system"""
    print("🚀 Starting LifeConnect Complete Backend System")
    print("=" * 60)
    
    # Check if required files exist
    required_files = [
        'app.py',
        'requirements.txt'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Missing file: {file}")
            return False
    
    # Install requirements
    print("📦 Installing requirements...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Requirements installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False
    
    # Start the backend
    print("🏃 Starting backend server...")
    try:
        # Set environment variables
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        
        # Start the app
        subprocess.run([sys.executable, 'app.py'])
        
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped by user")
    except Exception as e:
        print(f"❌ Backend startup error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = start_backend()
    if not success:
        exit(1)
