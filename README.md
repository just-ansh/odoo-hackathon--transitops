# 🚛 TransitOps — Smart Transport Operations Platform

TransitOps is a modern, high-performance web application designed to manage dispatch logistics, vehicle operations, fuel efficiency, driver performance, and financial analytics for cargo transportation fleets.

---

## 📁 Repository Structure
The repository is organized into two primary folders:
* **[`backend/`](file:///d:/odoo-hack/backend)**: FastAPI Python server using raw `psycopg` SQL for optimal performance.
* **[`frontend/`](file:///d:/odoo-hack/frontend)**: Vite-React SPA styled with Tailwind CSS, Recharts for visuals, and custom theme layouts.

---

## 🛠️ Getting Started & Setup Instructions

### 1. Database Setup (PostgreSQL)
Ensure you have a PostgreSQL server running locally or accessible on your network.
1. Create a database named `transitops`.
2. Configure your connection settings. The default configuration is in `backend/core/database.py`. You can override it dynamically by setting the `DATABASE_URL` environment variable:
   ```bash
   # Windows PowerShell
   $env:DATABASE_URL="host=localhost dbname=transitops user=postgres password=YOUR_PASSWORD port=5432"
   
   # Linux/macOS
   export DATABASE_URL="host=localhost dbname=transitops user=postgres password=YOUR_PASSWORD port=5432"
   ```

### 2. Backend Server Installation
Navigate into the `backend/` directory and configure the environment:
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate
   # Linux/macOS:
   source venv/bin/activate
   ```
2. Install the backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the database schema & seed initial configurations:
   ```bash
   # Run the unit test suite which rebuilds schema.sql and seed.sql
   python test_db.py
   ```
4. Seed the database with the **30-vehicle demo dataset** (includes trips, fuel logs, and maintenance logs):
   ```bash
   python scripts/seed_demo_data.py
   ```
5. Start the FastAPI backend server using Uvicorn:
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```
   * The backend API documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Frontend Installation
Navigate into the `frontend/` directory:
1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the Vite React development server:
   ```bash
   npm run dev
   ```
   * The web application will launch at: [http://localhost:5173](http://localhost:5173)

---

## 🔑 Pre-Seeded User Logins
Use these accounts to test the Role-Based Access Control (RBAC) layers on the platform. **Default Password for all accounts is: `1234`**

| Role | Email | Permissions / Features |
| :--- | :--- | :--- |
| **Fleet Manager** | `manager@transitops.com` | Full platform capabilities (CRUD vehicles, drivers, dispatches, financial metrics). |
| **Driver** | `driver@transitops.com` | View dispatches and execute trip completion entries. |
| **Safety Officer** | `safety@transitops.com` | Manage vehicle maintenance logs (open/close entries). |
| **Financial Analyst** | `finance@transitops.com` | View financial ROI breakdowns, record fuel logs, and submit operations expenses. |

---

## 💡 Key Platform Capabilities & QoL Features
* **Stateless Token Auth**: Protected endpoints validated via JWT security.
* **Offline Caching**: Automatically saves data requests in `localStorage`. If the backend database server is disconnected, the site falls back to cached data, enters **Read-Only Mode**, and shows a running duration counter of the database outage.
* **Responsive Visual Charts**: Customized high-contrast tooltips and gridlines supporting automatic Light and Dark Mode adjustments.
* **Visual Pagination Slider**: Easily pages through hundreds of registered vehicles inside the ROI reports chart, preventing label clutter.
