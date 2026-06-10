"""
V Launcher - Main entry point.
Starts the Python backend server and opens the 3D orb UI window.
"""
import os
import sys
import time
import threading
import signal

def main():
    # Set up paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    brain_dir = os.path.join(project_root, 'brain')
    sys.path.insert(0, brain_dir)
    
    # Change to project root
    os.chdir(project_root)
    
    print("=" * 50)
    print("    V LAUNCHER")
    print("    Starting server + UI...")
    print("=" * 50)
    
    # Start the FastAPI server in a background thread
    def run_server():
        import uvicorn
        from v_engine import app
        uvicorn.run(app, host="127.0.0.1", port=8888, log_level="info")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to be ready
    print("[Launcher] Waiting for server to start...")
    import urllib.request
    for i in range(30):  # Try for up to 15 seconds
        try:
            urllib.request.urlopen("http://127.0.0.1:8888/", timeout=1)
            print("[Launcher] Server is ready!")
            break
        except Exception:
            time.sleep(0.5)
    else:
        print("[Launcher] WARNING: Server may not be ready yet...")
    
    print("=" * 50)
    print("    V IS NOW RUNNING SILENTLY IN THE BACKGROUND")
    print("    (No UI Window will pop up)")
    print("    Press Ctrl+C to stop.")
    print("=" * 50)
    
    # Keep the process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down V...")


if __name__ == "__main__":
    main()
