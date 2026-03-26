CREATE TABLE IF NOT EXISTS regions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS teams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    region_id INT NULL,
    team_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    task_date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    hours DECIMAL(5,2) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tasks_user FOREIGN KEY (user_id) REFERENCES users(id)
);

ALTER TABLE users
ADD CONSTRAINT fk_users_region FOREIGN KEY (region_id) REFERENCES regions(id);

ALTER TABLE users
ADD CONSTRAINT fk_users_team FOREIGN KEY (team_id) REFERENCES teams(id);

INSERT IGNORE INTO regions (id, name) VALUES
(1, 'APAC'),
(2, 'EMEA'),
(3, 'NA'),
(4, 'LATAM');

INSERT IGNORE INTO teams (id, name) VALUES
(1, 'Production Support'),
(2, 'Application Support'),
(3, 'Incident Management'),
(4, 'Client Connectivity Support'),
(5, 'Other');

INSERT INTO users (
    username,
    email,
    password_hash,
    role,
    region_id,
    team_id
)
VALUES (
    'admin',
    'admin@test.com',
    'scrypt:32768:8:1$QUfXHxmZSp9enTn6$08e2766b7d364093aa8718d6db386f65c30f747f9d1086ea89a3d9aa378358a0fe5d4b943bcfcea64adfba72252f37f49059f9b1b5713074d8eb68bef1e18247', -- password = 123456
    'admin',
    1,
    1
);