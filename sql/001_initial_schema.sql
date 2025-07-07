-- BankBot Initial Database Schema
-- This script creates the initial database schema with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Create bank_documents table with vector column
CREATE TABLE IF NOT EXISTS bank_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    extracted_text TEXT,
    embedding VECTOR(1024),  -- Vector column for embeddings
    document_type VARCHAR(50),
    access_level INTEGER DEFAULT 1,  -- Access level 1-5 based on document type
    document_metadata TEXT,  -- JSON metadata
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for bank_documents table
CREATE INDEX IF NOT EXISTS idx_bank_documents_user_id ON bank_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_bank_documents_document_type ON bank_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_bank_documents_is_processed ON bank_documents(is_processed);
CREATE INDEX IF NOT EXISTS idx_bank_documents_created_at ON bank_documents(created_at);

-- Create vector similarity search index (using HNSW algorithm)
CREATE INDEX IF NOT EXISTS idx_bank_documents_embedding ON bank_documents 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    document_id UUID REFERENCES bank_documents(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    details TEXT,  -- JSON details
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    status VARCHAR(20) DEFAULT 'success',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit_logs table
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_document_id ON audit_logs(document_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Create function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at column
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bank_documents_updated_at
    BEFORE UPDATE ON bank_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create a function for vector similarity search
CREATE OR REPLACE FUNCTION search_documents_by_embedding(
    query_embedding VECTOR(1024),
    similarity_threshold FLOAT DEFAULT 0.5,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE(
    id UUID,
    filename VARCHAR(255),
    document_type VARCHAR(50),
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bd.id,
        bd.filename,
        bd.document_type,
        1 - (bd.embedding <=> query_embedding) as similarity
    FROM bank_documents bd
    WHERE bd.embedding IS NOT NULL
        AND bd.is_processed = TRUE
        AND (1 - (bd.embedding <=> query_embedding)) > similarity_threshold
    ORDER BY bd.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Insert sample data (optional for testing)
-- CREATE SAMPLE ADMIN USER (Password: admin123)
-- Note: In production, use proper password hashing
INSERT INTO users (username, email, password_hash, is_admin) 
VALUES ('admin', 'admin@bankbot.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewDBdGjlcFzxDOFK', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Create database constraints and additional indexes as needed
-- Add any additional setup queries here

COMMENT ON TABLE users IS 'User accounts for BankBot application';
COMMENT ON TABLE bank_documents IS 'Bank documents with vector embeddings for semantic search';
COMMENT ON TABLE audit_logs IS 'Audit trail for user actions and system events';
COMMENT ON COLUMN bank_documents.embedding IS 'Vector embedding for semantic similarity search';
COMMENT ON FUNCTION search_documents_by_embedding IS 'Search documents using vector similarity'; 