#!/usr/bin/env python3
"""
Quick startup script for both backend and frontend servers.
"""
import subprocess
import sys
import os
import time
import signal
import threading

def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting FastAPI backend server...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("Backend server stopped.")

def start_frontend():
    """Start the React frontend server."""
    print("🚀 Starting React frontend server...")
    try:
        os.chdir("frontend")
        subprocess.run(["npm", "start"], check=True)
    except KeyboardInterrupt:
        print("Frontend server stopped.")

if __name__ == "__main__":
    print("🎯 Starting CERONIX Supply Chain Risk Analysis System...")
    print("=" * 60)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        sys.exit(0)
