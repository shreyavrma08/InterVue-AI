CREATE DATABASE IF NOT EXISTS ai_interviewer;
USE ai_interviewer;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'admin') DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Fields Table
CREATE TABLE IF NOT EXISTS fields (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- 3. Subjects Table
CREATE TABLE IF NOT EXISTS subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    field_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
);

-- 4. Topics Table
CREATE TABLE IF NOT EXISTS topics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- 5. Questions Table (Main Question Bank)
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    question_text TEXT NOT NULL,
    difficulty ENUM('basic', 'intermediate', 'advanced') NOT NULL,
    explanation TEXT,
    source ENUM('manual', 'ai_generated', 'external_api') DEFAULT 'manual',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- 6. Question Options Table
CREATE TABLE IF NOT EXISTS question_options (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- 7. Assessments Table
CREATE TABLE IF NOT EXISTS assessments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    subject_id INT NOT NULL,
    assessment_type ENUM('full_placement', 'topic_practice', 'ai_personalized') DEFAULT 'full_placement',
    total_questions INT NOT NULL,
    duration_minutes INT DEFAULT 45,
    status ENUM('in_progress', 'completed', 'abandoned') DEFAULT 'in_progress',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- 8. Assessment Questions Link Table
CREATE TABLE IF NOT EXISTS assessment_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL,
    question_id INT NOT NULL,
    question_order INT NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- 9. User Answers Table
CREATE TABLE IF NOT EXISTS user_answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL,
    question_id INT NOT NULL,
    selected_option_id INT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (selected_option_id) REFERENCES question_options(id) ON DELETE SET NULL
);

-- 10. Assessment Results Table
CREATE TABLE IF NOT EXISTS results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL UNIQUE,
    user_id INT NOT NULL,
    score DECIMAL(5, 2) NOT NULL,
    accuracy_rate DECIMAL(5, 2) NOT NULL,
    total_questions INT NOT NULL,
    attempted_questions INT NOT NULL,
    correct_answers INT NOT NULL,
    incorrect_answers INT NOT NULL,
    unattempted_questions INT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 11. Staging AI Questions Table (for Admin Review)
CREATE TABLE IF NOT EXISTS ai_question_staging (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic_id INT NOT NULL,
    question_text TEXT NOT NULL,
    difficulty ENUM('basic', 'intermediate', 'advanced') NOT NULL,
    options_json JSON NOT NULL, -- Format: [{"text": "...", "is_correct": true}]
    explanation TEXT,
    validation_status ENUM('pending', 'valid', 'invalid') DEFAULT 'pending',
    validation_reason VARCHAR(255),
    status ENUM('staged', 'approved', 'rejected') DEFAULT 'staged',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- SEED DATA SETUP
INSERT INTO fields (id, name, description) VALUES 
(1, 'Technical Placement', 'Software engineering, database architecture, and full-stack web technology tracks.'),
(2, 'Sales & Marketing Placement', 'Digital marketing strategy, search engine optimization, and corporate B2B sales pipelines.');

INSERT INTO subjects (id, field_id, name, description) VALUES
(1, 1, 'Data Structures & Algorithms', 'Core computational logic, memory efficiency, and complex problem-solving.'),
(2, 1, 'Relational Databases & SQL', 'Database normalization, SQL queries, join conditions, and optimization.'),
(3, 1, 'Web Development & APIs', 'Client-server communications, HTTP protocols, security tokens, and web interfaces.'),
(4, 2, 'Digital Marketing & Growth', 'Online customer acquisition, content marketing strategies, and conversion rate optimization.'),
(5, 2, 'B2B Sales & Account Management', 'Enterprise sales strategies, lead prospecting, value pitches, and deal closing.');

INSERT INTO topics (id, subject_id, name, description) VALUES
(1, 1, 'Arrays & HashMaps', 'Linear arrays, key-value lookup strategies, and collision resolution.'),
(2, 1, 'Linked Lists & Trees', 'Dynamic pointer chains, binary tree traversals, and search node balancing.'),
(3, 1, 'Dynamic Programming & Graphs', 'Memoization technique, graph search algorithms (BFS/DFS), and shortest path problems.'),
(4, 2, 'Basic Queries & Joins', 'SELECT, WHERE, INNER JOIN, LEFT JOIN, and table relationship mapping.'),
(5, 2, 'Subqueries & Aggregations', 'GROUP BY, HAVING, subqueries, and window functions.'),
(6, 2, 'Indexing & Performance Tuning', 'B-Tree indices, query execution plans, transactions, and lock escalations.'),
(7, 3, 'REST Architecture & HTTP', 'REST principles, status codes, request methods, and CORS security.'),
(8, 3, 'Frontend Foundations', 'DOM manipulation, modern JavaScript async mechanics, and CSS layouts.'),
(9, 3, 'Backend Systems & Auth', 'FastAPI/Node routing, JWT authentication, state management, and sessions.'),
(10, 4, 'SEO & Content Strategy', 'On-page technical SEO, search keywords, and inbound content marketing.'),
(11, 4, 'Paid Ads & PPC', 'PPC bidding engines, ad quality score optimization, and audience targeting.'),
(12, 4, 'Analytics & Conversion Funnels', 'Google Analytics setup, user attribution modeling, and funnel conversion optimization.'),
(13, 5, 'Lead Generation & Prospecting', 'Inbound sales qualified leads, outbound email campaigns, and prospecting techniques.'),
(14, 5, 'Objection Handling & Pitching', 'Overcoming price objections, selling value, and product demonstrations.'),
(15, 5, 'CRM & Pipeline Management', 'HubSpot/Salesforce metrics, sales stages, deal velocities, and forecasting accuracy.');