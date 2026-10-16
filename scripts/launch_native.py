#!/usr/bin/env python3
"""
Native Launcher for DroneIMS
Starts PostgreSQL, MinIO, Backend, and Frontend without Docker.
"""
import os
import sys
import subprocess
import time
import socket
import signal
import platform
import shutil
from pathlib import Path

# Configuration
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR
FRONTEND_DIR = ROOT_DIR / "web"
POSTGRES_DATA = ROOT_DIR / "data" / "postgres"
MINIO_DATA = ROOT_DIR / "data" / "minio"

# Env Variables (names match app/core/config.py; values already set in the
# environment or .env win over these local-dev defaults)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/droneims")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_ACCESS_KEY_ID", "minioadmin")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "minioadmin")
os.environ.setdefault("ENV", "dev")
os.environ.setdefault("VISION_MODEL_PATH", str(ROOT_DIR / "models" / "best.pt"))
os.environ.setdefault("LABEL_TEMPLATE_PATH", str(ROOT_DIR / "models" / "label_template.png"))
os.environ.setdefault("TEMP_DIR", str(ROOT_DIR / "temp"))

processes = []

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_command(cmd, cwd=None, shell=False):
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    proc = subprocess.Popen(cmd, cwd=cwd, shell=shell)
    processes.append(proc)
    return proc

def stop_services():
    print("\n🛑 Shutting down all services...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            p.kill()
    print("All services stopped.")

def setup_postgres():
    print("🐘 Checking PostgreSQL...")
    pg_ctl = shutil.which("pg_ctl")
    initdb = shutil.which("initdb")
    
    if not pg_ctl:
        # Try common Windows paths
        if platform.system() == "Windows":
            pg_paths = [
                r"C:\Program Files\PostgreSQL\16\bin",
                r"C:\Program Files\PostgreSQL\15\bin",
                r"C:\Program Files\PostgreSQL\14\bin"
            ]
            for p in pg_paths:
                if os.path.exists(p):
                    os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
                    pg_ctl = shutil.which("pg_ctl")
                    initdb = shutil.which("initdb")
                    break
    
    if not pg_ctl:
        print("❌ ERROR: PostgreSQL not found in PATH.")
        print("Please install PostgreSQL 14+ and add 'bin' folder to PATH.")
        sys.exit(1)

    if not os.path.exists(POSTGRES_DATA):
        print("Initializing database cluster...")
        os.makedirs(POSTGRES_DATA)
        if not initdb:
            print("❌ initdb not found. Re-check installation.")
            sys.exit(1)
        subprocess.run([initdb, "-D", str(POSTGRES_DATA)], check=True)
        
        # Set password
        # Note: In a real script we'd edit pg_hba.conf and postgresql.conf properly
        # For simplicity, we assume trust local or prompt user to set password manually if needed
        # Ideally, start once, set password, stop, then restart. 
        # Here we rely on the DB being created and the app using the connection string.
        print("Database cluster initialized.")

    print("Starting PostgreSQL...")
    # Start in background
    run_command([pg_ctl, "-D", str(POSTGRES_DATA), "-l", str(ROOT_DIR / "postgres.log"), "start"])
    
    # Wait for ready
    for _ in range(30):
        if check_port(5432):
            print("PostgreSQL is ready.")
            return True
        time.sleep(1)
    
    print("❌ Failed to start PostgreSQL.")
    return False

def setup_minio():
    print("☁️ Checking MinIO...")
    minio_bin = shutil.which("minio")
    
    if not minio_bin:
        # Auto-download for Windows/Linux/Mac if missing? 
        # For now, require installation or provide binary
        print("⚠️ MinIO binary not found in PATH.")
        print("Please install MinIO or download the binary to the project root.")
        # Fallback: Skip MinIO if not critical for immediate startup, or exit
        # Let's try to run assuming it might be installed globally
        minio_bin = "minio" 

    os.makedirs(MINIO_DATA, exist_ok=True)
    
    print("Starting MinIO...")
    cmd = [
        minio_bin, "server", str(MINIO_DATA),
        "--address", ":9000",
        "--console-address", ":9001"
    ]
    run_command(cmd)
    
    for _ in range(15):
        if check_port(9000):
            print("MinIO is ready.")
            return True
        time.sleep(1)
    return True # Continue anyway

def setup_db_tables():
    print("🛠 Running Database Migrations...")
    # Same schema path as Docker: apply Alembic migrations (alembic/versions).
    try:
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND_DIR, check=True
        )
        print("Database schema is up to date.")
    except Exception as e:
        print(f"⚠️ Could not run migrations: {e}")
        print("Run 'alembic upgrade head' manually before using the app.")


def create_admin_user():
    print("👤 Ensuring Super Admin exists...")
    script_path = ROOT_DIR / "scripts" / "create_superuser.py"
    if os.path.exists(script_path):
        try:
            subprocess.run([sys.executable, str(script_path)], check=True)
        except Exception as e:
            print(f"⚠️ Failed to create admin user automatically: {e}")
            print("You can run 'python scripts/create_superuser.py' manually.")
    else:
        print("⚠️ create_superuser.py not found.")

def start_backend():
    print("🚀 Starting FastAPI Backend...")
    os.chdir(BACKEND_DIR)
    # Use uvicorn
    run_command([
        sys.executable, "-m", "uvicorn", "app.main:app", 
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ])
    
    for _ in range(20):
        if check_port(8000):
            print("Backend is ready at http://localhost:8000")
            return True
        time.sleep(1)
    return False

def start_frontend():
    print("🎨 Starting Next.js Frontend...")
    os.chdir(FRONTEND_DIR)
    
    # Check node_modules
    if not os.path.exists(FRONTEND_DIR / "node_modules"):
        print("Installing Node dependencies...")
        run_command(["npm", "install"], cwd=FRONTEND_DIR)
        # Wait for install to finish (blocking)
        processes[-1].wait()
        processes.pop() # Remove install process from list

    run_command(["npm", "run", "dev"], cwd=FRONTEND_DIR)
    
    for _ in range(30):
        if check_port(3000):
            print("Frontend is ready at http://localhost:3000")
            return True
        time.sleep(1)
    return False

def main():
    print("🚁 DroneIMS Native Launcher")
    print("="*30)
    
    # Register signal handler
    def sig_handler(sig, frame):
        stop_services()
        sys.exit(0)
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    if not setup_postgres():
        sys.exit(1)
    
    setup_minio()
    setup_db_tables()
    create_admin_user()
    
    if not start_backend():
        print("Backend failed to start.")
        stop_services()
        sys.exit(1)
        
    if not start_frontend():
        print("Frontend failed to start.")
        stop_services()
        sys.exit(1)

    print("\n✅ System Ready!")
    print("Log in with the admin account created by scripts/create_superuser.py.")
    print("Press Ctrl+C to stop all services.\n")
    
    # Keep alive
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
