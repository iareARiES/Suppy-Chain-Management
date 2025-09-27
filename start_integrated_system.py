#!/usr/bin/env python3
"""
Startup script for the integrated CERONIX Supply Chain Risk Analysis System
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting CERONIX Backend API...")
    try:
        # Start the FastAPI server
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], cwd=os.getcwd())
        
        print("✅ Backend API started on http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/api/docs")
        return backend_process
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the React frontend development server."""
    print("🎨 Starting CERONIX Frontend...")
    try:
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print("❌ Frontend directory not found. Please create the React app first.")
            return None
            
        # Install dependencies if needed
        if not (frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        
        # Start the React development server
        frontend_process = subprocess.Popen([
            "npm", "start"
        ], cwd=frontend_dir)
        
        print("✅ Frontend started on http://localhost:3000")
        return frontend_process
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    # Check Python dependencies
    try:
        import fastapi
        import uvicorn
        import motor
        import pymongo
        print("✅ Python dependencies OK")
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()} installed")
        else:
            print("❌ Node.js not found. Please install Node.js")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found. Please install Node.js")
        return False
    
    # Check npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm {result.stdout.strip()} installed")
        else:
            print("❌ npm not found")
            return False
    except FileNotFoundError:
        print("❌ npm not found")
        return False
    
    return True

def main():
    """Main startup function."""
    print("🎯 CERONIX Supply Chain Risk Analysis System")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing dependencies.")
        return
    
    print("\n🚀 Starting integrated system...")
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        return
    
    print("\n🎉 System started successfully!")
    print("=" * 50)
    print("📊 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/api/docs")
    print("🎨 Frontend: http://localhost:3000")
    print("=" * 50)
    print("\nPress Ctrl+C to stop all services...")
    
    try:
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break
                
            if frontend_process and frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        
        # Terminate processes
        if backend_process:
            backend_process.terminate()
            print("✅ Backend stopped")
            
        if frontend_process:
            frontend_process.terminate()
            print("✅ Frontend stopped")
            
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
