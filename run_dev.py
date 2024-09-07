import subprocess
import sys
import time
from pathlib import Path

def run_command(command, cwd=None):
    return subprocess.Popen(command, cwd=cwd, shell=True)

def main():
    # Start the backend
    backend = run_command("python back/app.py")
    
    # Start the frontend
    frontend = run_command("npm run dev", cwd="front")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        backend.terminate()
        frontend.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
