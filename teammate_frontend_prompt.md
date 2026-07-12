# 🚀 TransitOps — Frontend Developer Prompt
# Developer 2 Setup Guide
# Smart Transport Operations Platform (Hackathon)

---

## ⚡ CONTEXT: What Has Already Been Built (Developer 1 — Backend)

You are **Developer 2** on a 2-person hackathon team building **TransitOps**, a Smart Transport
Operations Platform. The backend is fully built and running live on your teammate's machine.

### Backend Tech Stack (Already Deployed — Do NOT Rebuild)
- **Runtime**: Python + FastAPI + Uvicorn
- **Database**: PostgreSQL (raw SQL via `psycopg`, no ORM)
- **Hosting**: Hosted locally on your teammate's machine at IP `192.168.0.9`
- **Port**: `8000`

### Interactive API Docs
Your teammate's live Swagger UI is accessible at:
```
http://192.168.0.9:8000/docs
```
You can use this to test every endpoint from the browser and see full request/response schemas.

---

## 🎯 YOUR OBJECTIVE: Build the Frontend

Build a complete, modern, and responsive web frontend for TransitOps. It must consume the live
FastAPI backend hosted at `http://192.168.0.9:8000`.

### Tech Stack Decisions (Your Call — Recommended Stack Below)
- **Framework**: React (with Vite) or Next.js
- **Styling**: TailwindCSS or plain CSS
- **HTTP Client**: `fetch` API or `axios`
- **Charts/Analytics**: `recharts` or `chart.js` for ROI and metrics dashboards
- **Design**: Dark mode preferred. Make it look operational — like a real fleet management 
  dashboard. Think: sidebars, data tables, status badges, and live metric cards.

---

## 🗃️ DATABASE ENTITIES (What You Are Displaying)

The backend manages these core entities. Your UI needs to represent all of them:

### Vehicles
| Field               | Type    | Description                              |
|--------------------|---------|------------------------------------------|
| id                  | int     | Primary Key                              |
| registration_number | string  | Unique license plate                     |
| name_model          | string  | Vehicle name/model (e.g. "Ford F-550")   |
| type                | string  | Vehicle type (e.g. "Flatbed", "Hauler")  |
| max_load_capacity   | decimal | Max cargo in kg                          |
| odometer            | decimal | Current odometer reading                 |
| acquisition_cost    | decimal | Purchase cost (for ROI calculation)      |
| status              | enum    | `Available` / `On Trip` / `In Shop` / `Retired` |

### Drivers
| Field               | Type    | Description                              |
|--------------------|---------|------------------------------------------|
| id                  | int     | Primary Key                              |
| name                | string  | Full name                                |
| license_number      | string  | Unique CDL license number                |
| license_category    | string  | e.g. "Class A CDL"                       |
| license_expiry_date | date    | License expiry date                      |
| contact_number      | string  | Phone number                             |
| safety_score        | decimal | Score between 0.00 and 100.00            |
| status              | enum    | `Available` / `On Trip` / `Off Duty` / `Suspended` |

### Trips
| Field                | Type    | Description                              |
|---------------------|---------|------------------------------------------|
| id                   | int     | Primary Key                              |
| source               | string  | Origin location                          |
| destination          | string  | Destination location                     |
| vehicle_id           | int     | FK → Vehicle                             |
| driver_id            | int     | FK → Driver                              |
| cargo_weight         | decimal | Cargo weight in kg                       |
| planned_distance     | decimal | Planned trip distance                    |
| final_odometer       | decimal | Odometer at trip end (set on completion) |
| fuel_consumed_liters | decimal | Liters consumed (set on completion)      |
| revenue              | decimal | Trip revenue                             |
| status               | enum    | `Draft` / `Dispatched` / `Completed` / `Cancelled` |
| created_at           | datetime| Trip creation timestamp                  |

---

## 🔌 LIVE API ENDPOINTS

Base URL: `http://192.168.0.9:8000`

---

### POST `/api/dispatch` — Dispatch a New Trip
**Purpose**: Creates a new trip and locks the vehicle + driver to 'On Trip' status atomically.
```json
// Request Body
{
  "vehicle_id": 1,
  "driver_id": 1,
  "cargo_weight": 4500.0,
  "source": "Austin, TX",
  "destination": "Houston, TX",
  "planned_distance": 160.0,
  "revenue": 1200.0
}

// Success Response (201)
{
  "message": "Trip successfully dispatched",
  "trip": {
    "id": 3,
    "source": "Austin, TX",
    "destination": "Houston, TX",
    "vehicle_id": 1,
    "driver_id": 1,
    "cargo_weight": 4500.0,
    "planned_distance": 160.0,
    "revenue": 1200.0,
    "status": "Dispatched",
    "created_at": "2026-07-12T09:00:00Z"
  }
}
```

---

### POST `/api/complete` — Complete a Dispatched Trip
**Purpose**: Closes a trip, records odometer + fuel data, and frees vehicle + driver back to 'Available'.
```json
// Request Body
{
  "trip_id": 3,
  "final_odometer": 15160.0,
  "fuel_consumed": 55.5
}

// Success Response (200)
{
  "message": "Trip successfully completed",
  "trip": {
    "id": 3,
    "status": "Completed",
    "final_odometer": 15160.0,
    "fuel_consumed_liters": 55.5
  }
}
```

---

### POST `/api/maintenance` — Send Vehicle to Shop
**Purpose**: Switches vehicle status to 'In Shop' and opens a maintenance log entry.
```json
// Request Body
{
  "vehicle_id": 1,
  "description": "Transmission fluid replacement and routine check"
}

// Success Response (201)
{
  "message": "Vehicle successfully sent to shop",
  "maintenance_log": {
    "id": 1,
    "vehicle_id": 1,
    "description": "Transmission fluid replacement and routine check",
    "cost": 0.0,
    "status": "Open",
    "logged_at": "2026-07-12T09:05:00Z"
  }
}
```

---

### GET `/api/roi` — Fleet ROI Dashboard Metrics
**Purpose**: Returns fleet-wide financial performance metrics for the analytics dashboard.
```json
// Success Response (200)
{
  "roi_metrics": {
    "total_revenue": 2300.00,
    "total_maintenance_cost": 620.00,
    "total_fuel_cost": 277.50,
    "total_acquisition_cost": 220000.00,
    "fleet_roi": 0.0064
  }
}
```

---

### GET `/api/health` — Server Health Check
**Purpose**: Quick ping to confirm backend and DB are online.
```json
// Success Response (200)
{
  "status": "healthy",
  "database": "connected"
}
```

---

## ⚠️ ERROR HANDLING REFERENCE

The backend returns structured error responses. The frontend MUST handle these gracefully:

| HTTP Status | Meaning                        | Example Scenario                                |
|------------|--------------------------------|-------------------------------------------------|
| 400        | Business logic validation fail | Cargo exceeds vehicle capacity; driver not free |
| 404        | Entity not found               | Vehicle/Driver ID does not exist                |
| 500        | Server / Database error        | Connection failure                              |

All errors return JSON in this format:
```json
{
  "detail": "Vehicle 1 is 'On Trip', expected 'Available'."
}
```
Always display `response.detail` as a toast notification or alert in the UI.

---

## 🖥️ UI PAGES & FEATURES TO BUILD

### 1. 📊 Dashboard (Home Page)
- Summary cards: Total Vehicles, Available Drivers, Active Trips, Completed Trips today
- ROI metric card showing Fleet ROI % from `/api/roi`
- A bar or line chart showing revenue vs. costs (maintenance + fuel)
- Recent trips feed (from trips data)

### 2. 🚛 Fleet Management (Vehicles Page)
- Full table of all vehicles with status badges (color-coded)
  - 🟢 Available / 🟡 On Trip / 🔴 In Shop / ⚫ Retired
- Action button: "Send to Maintenance" (calls `POST /api/maintenance`)
- Display key metrics: odometer, max load, acquisition cost

### 3. 👤 Drivers Page
- Full table of all drivers with status badges and safety scores
  - 🟢 Available / 🟡 On Trip / 🔵 Off Duty / 🔴 Suspended
- Safety score visual indicator (progress bar or circular gauge)
- License expiry warning for expiring licenses (< 30 days)

### 4. 🗺️ Trips Page
- Full table of all trips with status badges
- "Dispatch Trip" button that opens a form modal calling `POST /api/dispatch`
  - Form must show only 'Available' vehicles and 'Available' drivers in dropdowns
- "Complete Trip" button per dispatched trip row (calls `POST /api/complete`)
  - Opens a small form for final odometer and fuel consumed

### 5. 💰 Analytics / ROI Page
- Large ROI metric display
- Cost breakdown pie/donut chart: Revenue vs. Maintenance Costs vs. Fuel Costs
- Per-vehicle cost breakdown (using trips + maintenance + fuel data)

---

## ✅ IMPORTANT NOTES

1. **CORS**: The backend is already configured to allow requests from `*`. No proxy setup required.
2. **Authentication**: There is no auth on the API for the hackathon. Skip login screens to save time.
3. **Real-Time Data**: Since there is no WebSocket, just poll `/api/health` and relevant endpoints
   every 10-15 seconds to keep the dashboard live.
4. **Status Badges**: Color-code all status values consistently:
   - `Available` → Green
   - `On Trip` → Amber/Yellow
   - `In Shop` → Red/Orange
   - `Retired` / `Suspended` → Gray
   - `Dispatched` → Blue
   - `Completed` → Green
   - `Cancelled` → Gray

---

## 🧑‍💻 QUICK START

1. Clone the repository: `git clone https://github.com/just-ansh/odoo-hackathon--transitops.git`
2. Create your frontend project inside a new directory (e.g., `frontend/`) in the repo root.
3. Set the API base URL as an environment variable or constant:
   ```js
   const API_BASE = "http://192.168.0.9:8000";
   ```
4. Test the backend connection by calling `GET /api/health` on load.
5. Start with the Dashboard page, then Fleet, Drivers, Trips, and Analytics.
