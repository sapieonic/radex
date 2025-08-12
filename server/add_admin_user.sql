-- Migration script to add admin user to existing database
-- Run this against your existing database

INSERT INTO users (email, username, hashed_password, is_active, is_superuser) 
VALUES (
    'admin@radex.local', 
    'admin', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewgF5W9rVq8uUWsS',
    true, 
    true
) ON CONFLICT (email) DO NOTHING;

-- Verify the admin user was created
SELECT id, email, username, is_active, is_superuser, created_at 
FROM users 
WHERE username = 'admin';