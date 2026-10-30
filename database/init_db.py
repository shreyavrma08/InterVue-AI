import pymysql
import os

# Database Connection Settings
DB_HOST = "localhost"
DB_USER = "root"          # Replace with your MySQL username
DB_PASSWORD = "password"  # Replace with your MySQL password
DB_NAME = "ai_interviewer"

def initialize_database():
    print("Connecting to MySQL server...")
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=True
    )
    
    with connection.cursor() as cursor:
        # Create Database if it doesn't exist
        print(f"Creating database '{DB_NAME}' if not exists...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
        cursor.execute(f"USE {DB_NAME};")

        # Create Tables
        print("Creating schema tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subject_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_question_staging (
                id INT AUTO_INCREMENT PRIMARY KEY,
                topic_id INT NOT NULL,
                question_text TEXT NOT NULL,
                difficulty VARCHAR(20) NOT NULL,
                options_json JSON NOT NULL,
                explanation TEXT,
                validation_status VARCHAR(20) DEFAULT 'pending',
                validation_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            );
        """)

        # Insert Initial Default Data (Seed Data)
        print("Seeding initial subjects and topics...")
        
        # Insert Subjects
        cursor.execute("INSERT IGNORE INTO subjects (id, name) VALUES (1, 'Data Structures'), (2, 'SQL & Databases');")
        
        # Insert Topics
        cursor.execute("""
            INSERT IGNORE INTO topics (id, subject_id, name) VALUES 
            (1, 1, 'Arrays & HashMaps'),
            (2, 1, 'Trees & Graphs'),
            (3, 2, 'Basic Queries'),
            (4, 2, 'Joins & Subqueries');
        """)

    connection.close()
    print("Database setup completed successfully!")

if __name__ == "__main__":
    initialize_database()