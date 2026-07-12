-- TransitOps Database Schema (sql/schema.sql)
-- Act as an expert Senior Database Architect

DROP TABLE IF EXISTS expenses CASCADE;
DROP TABLE IF EXISTS fuel_logs CASCADE;
DROP TABLE IF EXISTS maintenance_logs CASCADE;
DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS drivers CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

DROP TYPE IF EXISTS expense_type CASCADE;
DROP TYPE IF EXISTS maintenance_status CASCADE;
DROP TYPE IF EXISTS trip_status CASCADE;
DROP TYPE IF EXISTS driver_status CASCADE;
DROP TYPE IF EXISTS vehicle_status CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;

-- Create Custom Enums
CREATE TYPE user_role AS ENUM (
    'Fleet Manager', 
    'Driver', 
    'Safety Officer', 
    'Financial Analyst'
);

CREATE TYPE vehicle_status AS ENUM (
    'Available', 
    'On Trip', 
    'In Shop', 
    'Retired'
);

CREATE TYPE driver_status AS ENUM (
    'Available', 
    'On Trip', 
    'Off Duty', 
    'Suspended'
);

CREATE TYPE trip_status AS ENUM (
    'Draft', 
    'Dispatched', 
    'Completed', 
    'Cancelled'
);

CREATE TYPE maintenance_status AS ENUM (
    'Open', 
    'Closed'
);

CREATE TYPE expense_type AS ENUM (
    'Tolls', 
    'Maintenance', 
    'Other'
);

-- Users Table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Vehicles Table
CREATE TABLE vehicles (
    id BIGSERIAL PRIMARY KEY,
    registration_number VARCHAR(50) UNIQUE NOT NULL,
    name_model VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    max_load_capacity NUMERIC(10, 2) NOT NULL CHECK (max_load_capacity > 0),
    odometer NUMERIC(10, 2) DEFAULT 0.0 NOT NULL CHECK (odometer >= 0),
    acquisition_cost NUMERIC(12, 2) NOT NULL CHECK (acquisition_cost >= 0),
    status vehicle_status DEFAULT 'Available' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Drivers Table
CREATE TABLE drivers (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    license_number VARCHAR(50) UNIQUE NOT NULL,
    license_category VARCHAR(20) NOT NULL,
    license_expiry_date DATE NOT NULL,
    contact_number VARCHAR(20) NOT NULL,
    safety_score NUMERIC(5, 2) DEFAULT 100.00 NOT NULL CHECK (safety_score >= 0.00 AND safety_score <= 100.00),
    status driver_status DEFAULT 'Available' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Trips Table
CREATE TABLE trips (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(150) NOT NULL,
    destination VARCHAR(150) NOT NULL,
    vehicle_id BIGINT REFERENCES vehicles(id) ON DELETE RESTRICT NOT NULL,
    driver_id BIGINT REFERENCES drivers(id) ON DELETE RESTRICT NOT NULL,
    cargo_weight NUMERIC(10, 2) NOT NULL CHECK (cargo_weight >= 0),
    planned_distance NUMERIC(10, 2) NOT NULL CHECK (planned_distance > 0),
    final_odometer NUMERIC(10, 2) CHECK (final_odometer >= 0),
    fuel_consumed_liters NUMERIC(10, 2) CHECK (fuel_consumed_liters >= 0),
    revenue NUMERIC(12, 2) DEFAULT 0.0 NOT NULL CHECK (revenue >= 0),
    status trip_status DEFAULT 'Draft' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraint validation
    CONSTRAINT chk_final_odometer_nullability CHECK (
        (status = 'Completed' AND final_odometer IS NOT NULL) OR
        (status != 'Completed')
    )
);

-- Maintenance Logs Table
CREATE TABLE maintenance_logs (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT REFERENCES vehicles(id) ON DELETE CASCADE NOT NULL,
    description TEXT NOT NULL,
    cost NUMERIC(12, 2) DEFAULT 0.00 NOT NULL CHECK (cost >= 0),
    status maintenance_status DEFAULT 'Open' NOT NULL,
    logged_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    closed_at TIMESTAMPTZ,
    
    CONSTRAINT chk_closed_at CHECK (
        (status = 'Closed' AND closed_at IS NOT NULL) OR 
        (status = 'Open' AND closed_at IS NULL)
    )
);

-- Fuel Logs Table
CREATE TABLE fuel_logs (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT REFERENCES vehicles(id) ON DELETE CASCADE NOT NULL,
    trip_id BIGINT REFERENCES trips(id) ON DELETE SET NULL,
    liters NUMERIC(10, 2) NOT NULL CHECK (liters > 0),
    cost NUMERIC(12, 2) NOT NULL CHECK (cost >= 0),
    logged_date DATE DEFAULT CURRENT_DATE NOT NULL
);

-- Expenses Table
CREATE TABLE expenses (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT REFERENCES vehicles(id) ON DELETE CASCADE NOT NULL,
    type expense_type NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    description TEXT NOT NULL,
    logged_date DATE DEFAULT CURRENT_DATE NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_trips_vehicle_id ON trips(vehicle_id);
CREATE INDEX idx_trips_driver_id ON trips(driver_id);
CREATE INDEX idx_maintenance_logs_vehicle_id ON maintenance_logs(vehicle_id);
CREATE INDEX idx_fuel_logs_vehicle_id ON fuel_logs(vehicle_id);
CREATE INDEX idx_fuel_logs_trip_id ON fuel_logs(trip_id);
CREATE INDEX idx_expenses_vehicle_id ON expenses(vehicle_id);

CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_drivers_status ON drivers(status);
CREATE INDEX idx_trips_status ON trips(status);
