-- SQL script to create database and user for SMS Service
-- Run this as PostgreSQL superuser

-- Create database
CREATE DATABASE sms_service_db;

-- Create user (replace password)
CREATE USER sms_user WITH PASSWORD 'your_secure_password_here';

-- Grant all privileges on database
GRANT ALL PRIVILEGES ON DATABASE sms_service_db TO sms_user;

-- Connect to the database
\c sms_service_db;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO sms_user;
GRANT CREATE ON SCHEMA public TO sms_user;

-- Note: After running this script, update your .env file with:
-- DATABASE_URL=postgresql://sms_user:your_secure_password_here@localhost:5432/sms_service_db