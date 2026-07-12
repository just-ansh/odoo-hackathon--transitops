-- TransitOps Seed Data (sql/seed.sql)
-- Act as an expert Senior Database Architect

TRUNCATE TABLE expenses, fuel_logs, maintenance_logs, trips, drivers, vehicles, users RESTART IDENTITY CASCADE;

-- 1. Seed 1 User
INSERT INTO users (email, password_hash, role) VALUES
('manager@transitops.com', '$2b$12$K3h8jF2h8sh12H7skdJ18uKj28skdh182Hksla7d8shw12sh12sha', 'Fleet Manager');

-- 2. Seed 5 Available Vehicles
INSERT INTO vehicles (registration_number, name_model, type, max_load_capacity, odometer, acquisition_cost, status, region) VALUES
('DL-01-A-1234', 'Tata Prima 4025.S', 'Truck', 25000.00, 15000.00, 75000.00, 'Available', 'Delhi NCR'),
('MH-02-B-5678', 'Mahindra Blazo X 35', 'Truck', 35000.00, 25000.00, 145000.00, 'Available', 'Mumbai Region'),
('KA-03-C-9012', 'Tata Winger Cargo', 'Van', 1500.00, 8000.00, 35000.00, 'Available', 'Bangalore South'),
('TN-04-D-3456', 'Ashok Leyland Dost+', 'Van', 1800.00, 9000.00, 38000.00, 'Available', 'Chennai Coastal'),
('WB-05-E-7890', 'BharatBenz 2823R', 'Truck', 28000.00, 12000.00, 155000.00, 'Available', 'Kolkata East');

-- 3. Seed 5 Available Drivers
INSERT INTO drivers (name, license_number, license_category, license_expiry_date, contact_number, safety_score, status) VALUES
('Rajesh Kumar', 'DL-1420200012345', 'CDL-A', '2028-12-31', '+91-98765-43210', 98.50, 'Available'),
('Amit Singh', 'MH-4320190054321', 'CDL-A', '2029-06-30', '+91-91234-56789', 99.80, 'Available'),
('Srinivas Rao', 'KA-5120180098765', 'CDL-B', '2028-06-30', '+91-88888-88888', 95.00, 'Available'),
('Ananya Patel', 'GJ-0120210067890', 'CDL-B', '2029-01-15', '+91-77777-77777', 97.20, 'Available'),
('Vikram Chatterjee', 'WB-0220220024680', 'CDL-A', '2030-03-22', '+91-99999-99999', 99.00, 'Available');
