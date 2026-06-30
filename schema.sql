-- PostgreSQL Compatible Schema DDL for EduGenie
-- Based on the ERD Specifications

-- 1. USER Table
CREATE TABLE IF NOT EXISTS "user" (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. USER_QUERY Table
CREATE TABLE IF NOT EXISTS user_query (
    query_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
    query_type VARCHAR(50) NOT NULL,
    query_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. AI_RESPONSE Table
CREATE TABLE IF NOT EXISTS ai_response (
    response_id SERIAL PRIMARY KEY,
    query_id INTEGER NOT NULL UNIQUE REFERENCES user_query(query_id) ON DELETE CASCADE,
    response_text TEXT NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. QUIZ Table
CREATE TABLE IF NOT EXISTS quiz (
    quiz_id SERIAL PRIMARY KEY,
    query_id INTEGER NOT NULL REFERENCES user_query(query_id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer VARCHAR(10) NOT NULL, -- e.g., 'A', 'B', 'C', or 'D'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. SUMMARY Table
CREATE TABLE IF NOT EXISTS summary (
    summary_id SERIAL PRIMARY KEY,
    query_id INTEGER NOT NULL REFERENCES user_query(query_id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. LEARNING_PATH Table
CREATE TABLE IF NOT EXISTS learning_path (
    path_id SERIAL PRIMARY KEY,
    query_id INTEGER NOT NULL REFERENCES user_query(query_id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    difficulty_level VARCHAR(50) NOT NULL, -- e.g., 'Beginner', 'Intermediate', 'Advanced'
    recommended_resources TEXT NOT NULL, -- Detailed roadmaps and resources
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_user_query_user_id ON user_query(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_response_query_id ON ai_response(query_id);
CREATE INDEX IF NOT EXISTS idx_quiz_query_id ON quiz(query_id);
CREATE INDEX IF NOT EXISTS idx_summary_query_id ON summary(query_id);
CREATE INDEX IF NOT EXISTS idx_learning_path_query_id ON learning_path(query_id);
