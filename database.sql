CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    father_name VARCHAR(100),
    phone VARCHAR(20),
    qualification VARCHAR(100),
    city VARCHAR(50),
    gender VARCHAR(10),
    blood VARCHAR(5),
    age INT,
    dob VARCHAR(20),
    driving_license VARCHAR(10),
    address TEXT
);

CREATE TABLE IF NOT EXISTS bike_brand (
    brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name VARCHAR(100) NOT NULL,
    brand_model VARCHAR(100) NOT NULL,
    year VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS bike (
    bike_no VARCHAR(20) PRIMARY KEY,
    brand_name VARCHAR(100),
    brand_model VARCHAR(100),
    bike_name VARCHAR(100),
    bike_seat VARCHAR(30),
    bike_engine VARCHAR(50),
    bike_category VARCHAR(30),
    bike_mileage VARCHAR(20),
    bike_mirror VARCHAR(5),
    bike_rent INT,
    bike_status VARCHAR(20) DEFAULT 'Available'
);

CREATE TABLE IF NOT EXISTS booking (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_username VARCHAR(50),
    customer_name VARCHAR(100),
    customer_phone VARCHAR(20),
    brand_name VARCHAR(100),
    brand_model VARCHAR(100),
    
    bike_no VARCHAR(20),
    bike_name VARCHAR(100),
    bike_category VARCHAR(30),
    bike_mileage VARCHAR(20),
    bike_rent INT,
    total_days INT,
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    booking_status VARCHAR(20) DEFAULT 'Booked'
);

-- Insert a default admin (password: admin123)
INSERT OR IGNORE INTO admin (username, password)
VALUES ('admin', '$2b$12$cHKsS.G8GBhG4thXW80skeBc/ElP5GzpKc9l7ooUotTPJooGZQ3hm');

UPDATE admin
SET password = '$2b$12$cHKsS.G8GBhG4thXW80skeBc/ElP5GzpKc9l7ooUotTPJooGZQ3hm'
WHERE username = 'admin'
    AND password = '$2b$12$KIXbwbMzpIQhCGVmhAnLxupK0iS7OvWb0rZJOz3b4DgVqkOpX0d8u';