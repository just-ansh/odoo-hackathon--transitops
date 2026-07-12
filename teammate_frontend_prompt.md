# 🚀 TransitOps — Frontend Developer Prompt (v2)
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

### Interactive API Sandbox (Swagger UI)
```
http://192.168.0.9:8000/docs
```
Test all endpoints, see full request/response schemas live.

### API Base URL
```js
const API_BASE = "http://192.168.0.9:8000";
```

---

## 🔒 AUTH SCOPE — EXPLICITLY AGREED AS OUT OF SCOPE

**Authentication (login + RBAC) is intentionally dropped for this hackathon build.**
Both team members have agreed to this trade-off due to the 8-hour time constraint.
All API endpoints are publicly accessible — no tokens or headers required.
Do NOT spend time building a login page. Start directly on the dashboard.

---

## 🗃️ DATABASE ENTITIES

### Vehicles
| Field                | Type    | Notes                                           |
|---------------------|---------|-------------------------------------------------|
| id                   | int     | Primary Key                                     |
| registration_number  | string  | **Unique**                                      |
| name_model           | string  | e.g. "Ford F-550 Super Duty"                    |
| type                 | string  | e.g. "Flatbed", "Heavy Hauler", "Box Truck"     |
| max_load_capacity    | decimal | In kg                                           |
| odometer             | decimal | Current odometer reading in km                  |
| acquisition_cost     | decimal | Purchase cost (used in ROI calculations)        |
| status               | enum    | `Available` / `On Trip` / `In Shop` / `Retired` |
| created_at           | datetime|                                                 |

### Drivers
| Field               | Type    | Notes                                                    |
|--------------------|---------|----------------------------------------------------------|
| id                  | int     | Primary Key                                              |
| name                | string  |                                                          |
| license_number      | string  | **Unique**                                               |
| license_category    | string  | e.g. "Class A CDL"                                       |
| license_expiry_date | date    | Warn if < 30 days from today                             |
| contact_number      | string  |                                                          |
| safety_score        | decimal | 0.00–100.00                                              |
| status              | enum    | `Available` / `On Trip` / `Off Duty` / `Suspended`       |
| created_at          | datetime|                                                          |

### Trips
| Field                | Type    | Notes                                           |
|---------------------|---------|-------------------------------------------------|
| id                   | int     | Primary Key                                     |
| source               | string  | Origin location                                 |
| destination          | string  | Destination location                            |
| vehicle_id           | int     | FK → Vehicle                                    |
| driver_id            | int     | FK → Driver                                     |
| cargo_weight         | decimal | In kg                                           |
| planned_distance     | decimal | In km                                           |
| final_odometer       | decimal | Nullable — set on completion                    |
| fuel_consumed_liters | decimal | Nullable — set on completion (liters)           |
| revenue              | decimal | Agreed revenue for this trip                    |
| status               | enum    | `Draft` / `Dispatched` / `Completed` / `Cancelled` |
| created_at           | datetime|                                                 |

### Maintenance Logs
| Field       | Type     | Notes                                  |
|------------|----------|----------------------------------------|
| id          | int      | Primary Key                            |
| vehicle_id  | int      | FK → Vehicle                           |
| description | string   |                                        |
| cost        | decimal  | Starts at 0.00, set when closed        |
| status      | enum     | `Open` / `Closed`                      |
| logged_at   | datetime |                                        |
| closed_at   | datetime | Nullable — set when status = 'Closed'  |

### Fuel Logs
| Field       | Type   | Notes                          |
|------------|--------|--------------------------------|
| id          | int    | Primary Key                    |
| vehicle_id  | int    | FK → Vehicle                   |
| trip_id     | int    | FK → Trip (nullable)           |
| liters      | decimal| Fuel amount in liters          |
| cost        | decimal| Fuel cost                      |
| logged_date | date   |                                |

### Expenses
| Field       | Type   | Notes                              |
|------------|--------|------------------------------------|
| id          | int    | Primary Key                        |
| vehicle_id  | int    | FK → Vehicle                       |
| type        | enum   | `Tolls` / `Maintenance` / `Other`  |
| amount      | decimal|                                    |
| description | string |                                    |
| logged_date | date   |                                    |

---

## 🔌 COMPLETE API REFERENCE

### Base URL: `http://192.168.0.9:8000`

All endpoints that return lists return a JSON array directly (no pagination wrapper for now).
All write endpoints return a `message` string and the created/updated object.

---

### 🟢 GET /api/health
Checks if backend + database are up.
```
// 200 — Everything healthy
{ "status": "healthy", "database": "connected" }

// 503 — API is UP but database is DOWN
{ "detail": "Database connection unhealthy: <reason>" }
```
> Poll this every 10 seconds. If you get `200`, show a green indicator.
> If you get `503`, show an amber "DB Unavailable" warning.
> Any other failure (network error, refused connection) means the backend itself is down — show a red "API Offline" banner.

---

### 🚛 VEHICLES

#### GET /api/vehicles
Returns all vehicles. Supports optional query filters.
```
GET /api/vehicles
GET /api/vehicles?status=Available
GET /api/vehicles?type=Flatbed
GET /api/vehicles?status=Available&type=Heavy+Hauler
```
Response: array of vehicle objects.

---

### 👤 DRIVERS

#### GET /api/drivers
Returns all drivers. Supports optional query filter.
```
GET /api/drivers
GET /api/drivers?status=Available
```
Response: array of driver objects.

---

### 🗺️ TRIPS

#### GET /api/trips
Returns all trips. Supports optional query filters.
```
GET /api/trips
GET /api/trips?status=Dispatched
GET /api/trips?vehicle_id=1
GET /api/trips?driver_id=2&status=Completed
```
Response: array of trip objects.

#### POST /api/dispatch
Dispatches a new trip (validates vehicle/driver availability and cargo capacity).
```json
// Request
{
  "vehicle_id": 1,
  "driver_id": 1,
  "cargo_weight": 4500.0,
  "source": "Austin, TX",
  "destination": "Houston, TX",
  "planned_distance": 160.0,
  "revenue": 1200.0
}

// 201 Response
{
  "message": "Trip successfully dispatched",
  "trip": {
    "id": 3, "source": "Austin, TX", "destination": "Houston, TX",
    "vehicle_id": 1, "driver_id": 1, "cargo_weight": 4500.0,
    "planned_distance": 160.0, "revenue": 1200.0,
    "status": "Dispatched", "created_at": "2026-07-12T09:00:00Z"
  }
}
```

#### POST /api/complete
Closes a dispatched trip with final odometer and fuel data.
> ⚠️ The field is `fuel_consumed_liters` — not `fuel_consumed`. Use exactly this name.
```json
// Request
{
  "trip_id": 3,
  "final_odometer": 15160.0,
  "fuel_consumed_liters": 55.5
}

// 200 Response
{
  "message": "Trip successfully completed",
  "trip": {
    "id": 3, "status": "Completed",
    "final_odometer": 15160.0, "fuel_consumed_liters": 55.5,
    "revenue": 1200.0, "created_at": "2026-07-12T09:00:00Z"
  }
}
```

---

### 🔧 MAINTENANCE

#### GET /api/maintenance
Returns all maintenance logs. Supports optional filters.
```
GET /api/maintenance
GET /api/maintenance?status=Open
GET /api/maintenance?vehicle_id=2
```
Response: array of maintenance log objects.

#### POST /api/maintenance/open
Sends a vehicle to the shop and opens a maintenance log.
```json
// Request
{
  "vehicle_id": 1,
  "description": "Transmission fluid replacement and routine check"
}

// 201 Response
{
  "message": "Vehicle successfully sent to shop",
  "maintenance_log": {
    "id": 1, "vehicle_id": 1,
    "description": "Transmission fluid replacement and routine check",
    "cost": 0.0, "status": "Open", "logged_at": "2026-07-12T09:05:00Z"
  }
}
```

#### POST /api/maintenance/close
Closes an open maintenance log and restores the vehicle to 'Available'.
```json
// Request
{
  "log_id": 1,
  "cost": 350.00
}

// 200 Response
{
  "message": "Maintenance log closed and vehicle restored to Available",
  "maintenance_log": {
    "id": 1, "vehicle_id": 1, "cost": 350.00,
    "status": "Closed", "closed_at": "2026-07-12T11:00:00Z"
  }
}
```

---

### ⛽ FUEL LOGS

#### GET /api/fuel-logs
Returns all fuel log entries. Supports optional filters.
```
GET /api/fuel-logs
GET /api/fuel-logs?vehicle_id=1
GET /api/fuel-logs?trip_id=3
```
Response: array of fuel log objects.

#### POST /api/fuel-logs
Records a fuel purchase for a vehicle.
```json
// Request
{
  "vehicle_id": 1,
  "liters": 80.0,
  "cost": 120.00,
  "logged_date": "2026-07-12",
  "trip_id": 3
}

// 201 Response
{
  "message": "Fuel log recorded",
  "fuel_log": {
    "id": 1, "vehicle_id": 1, "trip_id": 3,
    "liters": 80.0, "cost": 120.00, "logged_date": "2026-07-12"
  }
}
```

---

### 💸 EXPENSES

#### GET /api/expenses
Returns all expense entries. Supports optional filters.
```
GET /api/expenses
GET /api/expenses?vehicle_id=1
GET /api/expenses?type=Tolls
```
Response: array of expense objects.

#### POST /api/expenses
Records an operational expense for a vehicle.
```json
// Request
{
  "vehicle_id": 1,
  "type": "Tolls",
  "amount": 45.00,
  "description": "Toll charges on I-10 westbound",
  "logged_date": "2026-07-12"
}

// 201 Response
{
  "message": "Expense recorded",
  "expense": {
    "id": 1, "vehicle_id": 1, "type": "Tolls",
    "amount": 45.00, "description": "Toll charges on I-10 westbound",
    "logged_date": "2026-07-12"
  }
}
```

---

### 📊 ANALYTICS / ROI

#### GET /api/roi
Fleet-wide aggregated ROI.
```json
// 200 Response
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

#### GET /api/roi/vehicles
Per-vehicle ROI breakdown (for the analytics chart and table).
```json
// 200 Response
{
  "vehicle_roi_breakdown": [
    {
      "vehicle_id": 1,
      "registration_number": "TX-8800-V",
      "name_model": "Ford F-550 Super Duty",
      "type": "Flatbed",
      "acquisition_cost": 75000.00,
      "total_revenue": 2300.00,
      "total_maintenance_cost": 620.00,
      "total_fuel_cost": 277.50,
      "roi": 0.0190
    }
  ]
}
```

---

## ⚠️ ERROR HANDLING CONTRACT

All errors return this JSON structure:
```json
{ "detail": "Human-readable error message here." }
```

| HTTP Status | When It Fires                                           | Frontend Action                        |
|------------|----------------------------------------------------------|----------------------------------------|
| 400         | Business rule violated (busy resource, bad odometer, duplicate registration/license) | Show `response.detail` as a toast error |
| 404         | Vehicle/Driver/Trip ID does not exist                   | Show "Not found" in the form           |
| 500         | Unexpected database/server error                        | Show generic "Something went wrong"    |
| 503         | Database is unreachable (health check only)             | Show amber "Database Unavailable" pill |

### Unique Constraint Errors (400)
The following fields are unique in the database. Attempting to create a duplicate returns a `400`:
- `vehicles.registration_number` → `"Registration number already exists."`
- `drivers.license_number` → `"License number already exists."`

---

## 🖥️ UI PAGES & FEATURES

### 1. 📊 Dashboard
- Status summary cards: Total Vehicles, Available Drivers, Active (Dispatched) Trips, Trips Completed Today
- Fleet ROI card from `GET /api/roi`
- Bar chart: Revenue vs. Maintenance Costs vs. Fuel Costs (from roi_metrics)
- Recent trips list from `GET /api/trips?status=Dispatched`
- Health indicator polling `GET /api/health` every 10 seconds

### 2. 🚛 Fleet Management
- Table of all vehicles (`GET /api/vehicles`) with status badges
- Filter controls: by `status` and `type`
- "Send to Maintenance" button (calls `POST /api/maintenance/open`)
- "Close Maintenance" button for vehicles currently 'In Shop' with matching open logs

### 3. 👤 Drivers
- Table of all drivers (`GET /api/drivers`) with status badges and safety score bar
- Filter by status
- License expiry warning badge if `license_expiry_date` < 30 days from today

### 4. 🗺️ Trips
- Table of all trips (`GET /api/trips`) with status badges
- Filter by status
- "Dispatch Trip" button → modal form calling `POST /api/dispatch`
  - Vehicle dropdown: fetch `GET /api/vehicles?status=Available`
  - Driver dropdown: fetch `GET /api/drivers?status=Available`
- "Complete Trip" button per Dispatched trip row → modal calling `POST /api/complete`

### 5. 💰 Analytics
- Fleet ROI from `GET /api/roi`
- Per-vehicle ROI table + bar chart from `GET /api/roi/vehicles`
- Cost breakdown donut: Maintenance vs. Fuel vs. Revenue
- Fuel log history from `GET /api/fuel-logs`
- Expense log history from `GET /api/expenses`

---

## ✅ STATUS BADGE COLOR GUIDE

| Status        | Color         |
|--------------|---------------|
| Available     | 🟢 Green      |
| On Trip       | 🟡 Amber      |
| In Shop       | 🔴 Red-Orange |
| Retired       | ⚫ Gray       |
| Suspended     | ⚫ Gray       |
| Off Duty      | 🔵 Blue       |
| Dispatched    | 🔵 Blue       |
| Completed     | 🟢 Green      |
| Cancelled     | ⚫ Gray       |
| Draft         | 🔘 Light Gray |
| Open (maint.) | 🟠 Orange     |
| Closed (maint.)| 🟢 Green     |

---

## 🧑‍💻 QUICK START

```bash
# 1. Clone the shared repo
git clone https://github.com/just-ansh/odoo-hackathon--transitops.git
cd odoo-hackathon--transitops

# 2. Create your frontend project directory
mkdir frontend && cd frontend

# 3. Scaffold with Vite (React)
npx create-vite@latest . --template react
npm install

# 4. Install axios for HTTP requests
npm install axios

# 5. Set your API base
# In src/api.js or src/config.js:
export const API_BASE = "http://192.168.0.9:8000";

# 6. Verify backend connection
fetch(`${API_BASE}/api/health`).then(r => r.json()).then(console.log)

# 7. Start building — begin with the Dashboard page
npm run dev
```
