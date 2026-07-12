-- TransitOps Seed Data (sql/seed.sql)
-- Act as an expert Senior Database Architect

TRUNCATE TABLE expenses, fuel_logs, maintenance_logs, trips, drivers, vehicles, users RESTART IDENTITY CASCADE;

-- 1. Seed 1 User
INSERT INTO users (email, password_hash, role) VALUES
('manager@transitops.com', '$2b$12$K3h8jF2h8sh12H7skdJ18uKj28skdh182Hksla7d8shw12sh12sha', 'Fleet Manager');

-- 2. Seed 5 Available Vehicles
INSERT INTO vehicles (registration_number, name_model, type, max_load_capacity, odometer, acquisition_cost, status, region) VALUES
('TX-8800-V', 'Ford F-550 Super Duty', 'Flatbed', 6500.00, 15000.00, 75000.00, 'Available', 'Texas East'),
('TX-9900-V', 'Freightliner Cascadia', 'Heavy Hauler', 30000.00, 25000.00, 145000.00, 'Available', 'Texas West'),
('TX-1111-V', 'Ford Transit', 'Van', 1500.00, 8000.00, 35000.00, 'Available', 'Texas North'),
('TX-2222-V', 'Chevrolet Express', 'Van', 1800.00, 9000.00, 38000.00, 'Available', 'Texas South'),
('TX-3333-V', 'Peterbilt 389', 'Heavy Hauler', 30000.00, 12000.00, 155000.00, 'Available', 'Texas West');

-- 3. Seed 5 Available Drivers
INSERT INTO drivers (name, license_number, license_category, license_expiry_date, contact_number, safety_score, status) VALUES
('John Doe', 'CDL-TX-778', 'Class A CDL', '2028-12-31', '+1-555-0100', 98.50, 'Available'),
('Jane Smith', 'CDL-TX-990', 'Class A CDL', '2029-06-30', '+1-555-0200', 99.80, 'Available'),
('Bob Johnson', 'CDL-TX-111', 'Class B CDL', '2028-06-30', '+1-555-0300', 95.00, 'Available'),
('Alice Davis', 'CDL-TX-222', 'Class B CDL', '2029-01-15', '+1-555-0400', 97.20, 'Available'),
('Charlie Brown', 'CDL-TX-333', 'Class A CDL', '2030-03-22', '+1-555-0500', 99.00, 'Available');
