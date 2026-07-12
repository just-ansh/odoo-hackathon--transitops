-- TransitOps Seed Data (seed.sql)
-- Act as an expert Senior Database Architect

-- Clean out existing data to ensure repeatable runs
TRUNCATE TABLE expenses, fuel_logs, maintenance_logs, trips, drivers, vehicles, users RESTART IDENTITY CASCADE;

-- 1. SEED USERS
INSERT INTO users (email, password_hash, role) VALUES
('alice.manager@transitops.com', '$2b$12$K3h8jF2h8sh12H7skdJ18uKj28skdh182Hksla7d8shw12sh12sha', 'Fleet Manager'),
('bob.driver@transitops.com', '$2b$12$K3h8jF2h8sh12H7skdJ18uKj28skdh182Hksla7d8shw12sh12shb', 'Driver'),
('charlie.safety@transitops.com', '$2b$12$K3h8jF2h8sh12H7skdJ18uKj28skdh182Hksla7d8shw12sh12shc', 'Safety Officer'),
('diana.analyst@transitops.com', '$2b$12$K3h8jF2h8sh12H7skdJ18uKj28skdh182Hksla7d8shw12sh12shd', 'Financial Analyst');

-- 2. SEED VEHICLES
INSERT INTO vehicles (registration_number, name_model, type, max_load_capacity, odometer, acquisition_cost, status) VALUES
-- Vehicle 1: Available, Ready for trip
('TX-9988-A', 'Ford F-550 Super Duty', 'Flatbed Truck', 6500.00, 45200.50, 75000.00, 'Available'),
-- Vehicle 2: Currently on Trip
('TX-1234-B', 'Volvo FH16', 'Semi-Trailer', 25000.00, 120500.00, 160000.00, 'On Trip'),
-- Vehicle 3: In Shop
('TX-5678-C', 'Isuzu NPR-HD', 'Box Truck', 4000.00, 89100.20, 52000.00, 'In Shop'),
-- Vehicle 4: Retired
('TX-0001-X', 'Chevrolet Express 3500', 'Cargo Van', 1500.00, 310200.40, 32000.00, 'Retired'),
-- Vehicle 5: Available, for testing dispatch
('TX-7777-T', 'Freightliner Cascadia', 'Heavy Hauler', 30000.00, 15000.00, 145000.00, 'Available');

-- 3. SEED DRIVERS
INSERT INTO drivers (name, license_number, license_category, license_expiry_date, contact_number, safety_score, status) VALUES
-- Driver 1: Available
('John Doe', 'DL-TEX-99128', 'Class A CDL', '2028-06-30', '+1-555-0199', 95.50, 'Available'),
-- Driver 2: On Trip
('Jane Smith', 'DL-TEX-88374', 'Class A CDL', '2027-11-15', '+1-555-0188', 98.20, 'On Trip'),
-- Driver 3: Off Duty
('David Miller', 'DL-TEX-22834', 'Class B CDL', '2026-09-01', '+1-555-0122', 88.00, 'Off Duty'),
-- Driver 4: Suspended
('Robert Johnson', 'DL-TEX-11002', 'Class A CDL', '2025-03-12', '+1-555-0111', 65.00, 'Suspended'),
-- Driver 5: Available, for testing dispatch
('Sarah Connor', 'DL-TEX-77283', 'Class A CDL', '2029-12-31', '+1-555-0177', 100.00, 'Available');

-- 4. SEED TRIPS
-- Note: Vehicle 2 and Driver 2 are marked 'On Trip' above, so they should have a corresponding 'Dispatched' trip.
INSERT INTO trips (source, destination, vehicle_id, driver_id, cargo_weight, planned_distance, final_odometer, fuel_consumed_liters, revenue, status, created_at) VALUES
-- Trip 1: Completed. Vehicle 1 was used.
('Dallas, TX', 'Houston, TX', 1, 1, 4500.00, 240.00, 45200.50, 95.00, 1200.00, 'Completed', CURRENT_TIMESTAMP - INTERVAL '5 days'),
-- Trip 2: Currently Dispatched. Vehicle 2 and Driver 2.
('Austin, TX', 'San Antonio, TX', 2, 2, 18000.00, 80.00, NULL, NULL, 600.00, 'Dispatched', CURRENT_TIMESTAMP - INTERVAL '2 hours'),
-- Trip 3: Draft Trip (unassigned vehicle/driver)
('El Paso, TX', 'Dallas, TX', 5, 5, 12000.00, 635.00, NULL, NULL, 3200.00, 'Draft', CURRENT_TIMESTAMP - INTERVAL '1 day'),
-- Trip 4: Cancelled Trip
('Houston, TX', 'New Orleans, LA', 1, 3, 2000.00, 350.00, NULL, NULL, 0.00, 'Cancelled', CURRENT_TIMESTAMP - INTERVAL '10 days'),
-- Trip 5: Another Completed Trip for Vehicle 1 (historical)
('Houston, TX', 'Dallas, TX', 1, 1, 5000.00, 240.00, 44960.50, 90.00, 1100.00, 'Completed', CURRENT_TIMESTAMP - INTERVAL '12 days');

-- 5. SEED MAINTENANCE LOGS
INSERT INTO maintenance_logs (vehicle_id, description, cost, status, logged_at, closed_at) VALUES
-- Vehicle 3: Oil change and brake pads (Open - hence why status is In Shop)
(3, 'Routine oil change and front brake pad replacement', 450.00, 'Open', CURRENT_TIMESTAMP - INTERVAL '1 day', NULL),
-- Vehicle 1: Replaced alternator (Closed)
(1, 'Alternator replacement and battery load check', 620.00, 'Closed', CURRENT_TIMESTAMP - INTERVAL '15 days', CURRENT_TIMESTAMP - INTERVAL '14 days'),
-- Vehicle 2: Scheduled maintenance (Closed)
(2, 'Transmission fluid flush and differential service', 1200.00, 'Closed', CURRENT_TIMESTAMP - INTERVAL '30 days', CURRENT_TIMESTAMP - INTERVAL '29 days');

-- 6. SEED FUEL LOGS
INSERT INTO fuel_logs (vehicle_id, trip_id, liters, cost, logged_date) VALUES
-- Linked to Trip 1 (Completed, Vehicle 1)
(1, 1, 95.00, 142.50, CURRENT_DATE - 5),
-- Linked to Trip 5 (Completed, Vehicle 1)
(1, 5, 90.00, 135.00, CURRENT_DATE - 12),
-- Fuel purchase for Vehicle 2 during trip
(2, 2, 120.00, 186.00, CURRENT_DATE),
-- Fuel purchase not explicitly tied to a trip (General tank refill for Vehicle 5)
(5, NULL, 150.00, 232.50, CURRENT_DATE - 2);

-- 7. SEED EXPENSES
INSERT INTO expenses (vehicle_id, type, amount, description, logged_date) VALUES
-- Tolls for Vehicle 1
(1, 'Tolls', 45.00, 'Toll road charges for Dallas to Houston trip', CURRENT_DATE - 5),
-- Maintenance expense record matching log for Vehicle 1
(1, 'Maintenance', 620.00, 'Alternator replacement invoice #99283', CURRENT_DATE - 14),
-- Miscellaneous expense for Vehicle 2
(2, 'Other', 25.00, 'Driver meal and overnight parking allowance', CURRENT_DATE);
