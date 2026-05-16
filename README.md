# 🚁 Drone Inventory Management System (Standalone Enterprise Edition)

A high-performance, standalone inventory management system utilizing autonomous drones, computer vision (YOLOv8), and advanced analytics. This edition runs natively on Windows/Linux/macOS **without Docker**, featuring a one-click launcher that orchestrates PostgreSQL, MinIO, Backend, and Frontend services automatically.

## ✨ Key Features

### 🛡️ Security & Access
- **JWT Authentication**: Secure stateless sessions.
- **Role-Based Access Control (RBAC)**: Admin, Warehouse Manager, Operator, Viewer.
- **Super Admin Default**: Pre-configured secure access.

### 🤖 AI-Powered Vision Engine
- **Custom YOLOv8 Support**: Upload your own trained `.pt` weights for specific object detection.
- **Label Template Matching**: Upload a reference label image; the system learns to detect similar labels in drone footage.
- **Hybrid Decoding**: Automatically extracts:
  - **QR Codes & Barcodes** (via `pyzbar`)
  - **Text Content** (via `EasyOCR`) from detected label regions.

### 🏭 Core Operations
- **Drone Fleet Management**: Battery health, status tracking, maintenance logs.
- **Autonomous Missions**: Waypoint planning and execution.
- **3D Warehouse Visualization**: Real-time drone tracking on interactive maps.
- **Automated Reporting**: PDF/CSV generation with visual evidence.

### 🚀 Standalone Architecture
- **Zero-Config Launcher**: One script starts Database, Storage, API, and UI.
- **Native Performance**: No container overhead; direct hardware access.
- **Self-Healing**: Automatic service health checks and restarts.

---

## 📋 Prerequisites

Ensure the following are installed on your system **before** starting:

1. **Python 3.10+** (Check: `python --version`)
2. **Node.js 18+** (Check: `node --version`)
3. **PostgreSQL 16+** (Check: `psql --version`)
   - *Must be added to your system PATH.*
   - *Default user `postgres` must be accessible.*
4. **Git** (for cloning)

> **Note for Windows Users**: Ensure you run PowerShell or Command Prompt as **Administrator** for the initial setup if PostgreSQL needs initialization.

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/asmandstudio-ux/DroneInventoryManagmentSystem.git
cd DroneInventoryManagmentSystem

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

### 2. Install Dependencies
Install Python requirements (includes AI libraries):
```bash
cd web
npm install
cd ..

4. Configure Environment
The launcher auto-generates .env files on first run. However, you can manually customize app/.env and web/.env.local if needed.

---

## 🚀 Running the System (One-Click Start)
This is the only command you need to run to start the entire ecosystem (DB, Storage, Backend, Frontend).

On Windows
Double-click the DroneIMS_Native.cmd icon in the root folder.
OR run via terminal:
```powershell
python scripts\launch_native.py --start

On macOS/Linux
```bash
python scripts/launch_native.py --start

---

## What Happens Next?
**PostgreSQL Check**: Verifies DB is running; creates droneims database if missing.
**MinIO Check**: Ensures object storage is ready.
**Super Admin Creation**: Automatically creates the default admin user.
**Backend Start**: Launches FastAPI on http://localhost:8000.
**Frontend Start**: Launches Next.js on http://localhost:3000.
**Auto-Login**: Your browser opens automatically to the dashboard.

---

## 🔑 Default Credentials
Upon first launch, the system creates a Super Admin account:
Field               Value
Username            finsun2020
Password            AestheticS68742!

---

## 🧠 Using the AI Vision Module
To enable custom label detection and barcode reading:
1. Upload Custom YOLO Weights (Optional)
If you have a custom-trained model (best.pt):
Go to Settings > AI Models.
Upload your .pt file.
If skipped, the system uses the default generic object detection model.
2. Upload Label Template (Required for Specific Labels)
To teach the system what your inventory labels look like:
Go to Settings > Vision Templates.
Upload a clear image of a single label as a reference.
The system will use template matching to find similar labels in drone scans.
3. Run a Scan
Create a Mission and assign a drone.
Once images are uploaded/simulated, go to Scan Results.
The system will automatically:
Locate labels based on your template.
Decode QR/Barcodes inside those labels.
Extract text (OCR) from the label area.

---

## 🧪 Testing & QA
Run the automated test suite to verify your installation:
```bash
# Backend Tests
pytest tests/ -v

# Frontend Tests (requires Playwright)
cd web
npx playwright test

---

## 📂 Project Structure
TEXT:
DroneInventoryManagmentSystem/
├── app/                    # FastAPI Backend
│   ├── api/routes/         # API Endpoints (Auth, Drones, Vision)
│   ├── services/           # Business Logic (Vision Engine, Storage)
│   ├── db/                 # Database Models & Session
│   └── main.py             # App Entry Point
├── web/                    # Next.js Frontend
│   ├── src/app/            # Pages & Components
│   └── public/             # Static Assets
├── scripts/                # Automation Scripts
│   ├── launch_native.py    # 🚀 Main Launcher
│   └── create_superuser.py # User Initialization
├── data/                   # Persistent Data (DB files, MinIO blobs)
├── requirements.txt        # Python Dependencies
└── DroneIMS_Native.cmd     # Windows One-Click Icon

---

## 🛠️ Troubleshooting

PostgreSQL Connection Error
Ensure PostgreSQL service is running (services.msc on Windows).
Verify postgres user has no password or matches your .env.
Check if port 5432 is not blocked by firewall.
Module Not Found (OpenCV/YOLO)
Re-run pip install -r requirements.txt --force-reinstall.
On Windows, you may need to install Microsoft C++ Build Tools.
Port Already in Use
If 8000 or 3000 is busy, kill the process:
Windows: netstat -ano | findstr :8000 then taskkill /PID <ID> /F
Linux/Mac: lsof -ti:8000 | xargs kill -9

---

## 📄 License
Proprietary Software - Asmand Studio UX © 2024

---

## 🤝 Support
For enterprise support or custom AI model training, contact support@asmandstudio.com.
```
