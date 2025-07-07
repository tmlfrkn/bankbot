-- Access Level Matrix Compliant Schema
-- Bu migration Access Level Matrix'e tam uyumlu şema oluşturur

-- 1. Users tablosuna access_level ekleme
ALTER TABLE users ADD COLUMN IF NOT EXISTS access_level INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50);

-- Users tablosuna comment ekle
COMMENT ON COLUMN users.access_level IS 'User access level 1-5 (1=Public, 2=Internal, 3=Confidential, 4=Restricted, 5=Executive)';
COMMENT ON COLUMN users.role IS 'User role (Risk Analyst, Compliance Officer, Customer Service Manager, etc.)';

-- 2. Yeni access matrix uyumlu bank_documents tablosu oluştur
CREATE TABLE IF NOT EXISTS bank_documents_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Document identification
    source_url VARCHAR(500),
    source_filename VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL, -- DocumentType enum value
    
    -- Multiple content versions - ACCESS MATRIX COMPLIANCE
    content_full TEXT,
    content_summary TEXT,
    content_relevant TEXT,
    
    -- Multiple embeddings for different content versions
    embedding_full VECTOR(1024),
    embedding_summary VECTOR(1024), 
    embedding_relevant VECTOR(1024),
    
    -- Chunk information
    chunk_index INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 1,
    
    -- Metadata
    document_metadata JSONB,
    
    -- Processing information
    is_processed BOOLEAN DEFAULT FALSE,
    processing_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Indexes for performance
CREATE INDEX IF NOT EXISTS idx_bank_documents_v2_user_id ON bank_documents_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_bank_documents_v2_document_type ON bank_documents_v2(document_type);
CREATE INDEX IF NOT EXISTS idx_bank_documents_v2_source_filename ON bank_documents_v2(source_filename);
CREATE INDEX IF NOT EXISTS idx_bank_documents_v2_is_processed ON bank_documents_v2(is_processed);

-- 4. Vector similarity search indexes
CREATE INDEX IF NOT EXISTS idx_bank_documents_v2_embedding_full 
    ON bank_documents_v2 USING hnsw (embedding_full vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_bank_documents_v2_embedding_summary 
    ON bank_documents_v2 USING hnsw (embedding_summary vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_bank_documents_v2_embedding_relevant 
    ON bank_documents_v2 USING hnsw (embedding_relevant vector_cosine_ops);

-- 5. Comments for documentation
COMMENT ON TABLE bank_documents_v2 IS 'Access Level Matrix compliant document storage with multiple content versions';
COMMENT ON COLUMN bank_documents_v2.document_type IS 'Document type from AccessType enum (public_product_info, internal_procedures, risk_models, regulatory_docs, investigation_reports, executive_reports)';
COMMENT ON COLUMN bank_documents_v2.content_full IS 'Full content - accessible based on access matrix';
COMMENT ON COLUMN bank_documents_v2.content_summary IS 'Summary content - for users with summary access';
COMMENT ON COLUMN bank_documents_v2.content_relevant IS 'Relevant content - for users with relevant access';
COMMENT ON COLUMN bank_documents_v2.embedding_full IS 'Vector embedding for full content';
COMMENT ON COLUMN bank_documents_v2.embedding_summary IS 'Vector embedding for summary content';
COMMENT ON COLUMN bank_documents_v2.embedding_relevant IS 'Vector embedding for relevant content';

-- 6. Updated trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bank_documents_v2_updated_at 
    BEFORE UPDATE ON bank_documents_v2 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 7. Access Level Matrix as a database view for reference
CREATE OR REPLACE VIEW access_level_matrix AS
SELECT 
    'public_product_info' as document_type,
    1 as user_level, 'full' as access_type
UNION ALL SELECT 'public_product_info', 2, 'full'
UNION ALL SELECT 'public_product_info', 3, 'full'
UNION ALL SELECT 'public_product_info', 4, 'full'
UNION ALL SELECT 'public_product_info', 5, 'full'
UNION ALL SELECT 'internal_procedures', 1, 'none'
UNION ALL SELECT 'internal_procedures', 2, 'full'
UNION ALL SELECT 'internal_procedures', 3, 'full'
UNION ALL SELECT 'internal_procedures', 4, 'full'
UNION ALL SELECT 'internal_procedures', 5, 'full'
UNION ALL SELECT 'risk_models', 1, 'none'
UNION ALL SELECT 'risk_models', 2, 'none'
UNION ALL SELECT 'risk_models', 3, 'full'
UNION ALL SELECT 'risk_models', 4, 'summary'
UNION ALL SELECT 'risk_models', 5, 'full'
UNION ALL SELECT 'regulatory_docs', 1, 'none'
UNION ALL SELECT 'regulatory_docs', 2, 'summary'
UNION ALL SELECT 'regulatory_docs', 3, 'relevant'
UNION ALL SELECT 'regulatory_docs', 4, 'full'
UNION ALL SELECT 'regulatory_docs', 5, 'full'
UNION ALL SELECT 'investigation_reports', 1, 'none'
UNION ALL SELECT 'investigation_reports', 2, 'none'
UNION ALL SELECT 'investigation_reports', 3, 'none'
UNION ALL SELECT 'investigation_reports', 4, 'none'
UNION ALL SELECT 'investigation_reports', 5, 'full'
UNION ALL SELECT 'executive_reports', 1, 'none'
UNION ALL SELECT 'executive_reports', 2, 'none'
UNION ALL SELECT 'executive_reports', 3, 'none'
UNION ALL SELECT 'executive_reports', 4, 'summary'
UNION ALL SELECT 'executive_reports', 5, 'full';

COMMENT ON VIEW access_level_matrix IS 'Access Level Matrix reference - shows what access type each user level has for each document type';

-- 8. Helper function to check access
CREATE OR REPLACE FUNCTION check_user_access(
    p_user_level INTEGER,
    p_document_type VARCHAR(50)
) RETURNS VARCHAR(20) AS $$
BEGIN
    RETURN (
        SELECT access_type 
        FROM access_level_matrix 
        WHERE user_level = p_user_level 
        AND document_type = p_document_type
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_user_access IS 'Helper function to check what access type a user has for a document type';

-- 9. Sample test users with different access levels
INSERT INTO users (username, email, password_hash, access_level, role, is_active, is_admin) 
VALUES 
    ('public_user', 'public@bankbot.test', 'dummy_hash_public', 1, 'Public User', true, false),
    ('internal_user', 'internal@bankbot.test', 'dummy_hash_internal', 2, 'Internal Staff', true, false),
    ('confidential_user', 'confidential@bankbot.test', 'dummy_hash_confidential', 3, 'Risk Analyst', true, false),
    ('restricted_user', 'restricted@bankbot.test', 'dummy_hash_restricted', 4, 'Compliance Officer', true, false),
    ('executive_user', 'executive@bankbot.test', 'dummy_hash_executive', 5, 'Executive', true, true)
ON CONFLICT (username) DO NOTHING;

-- 10. Test the access matrix
SELECT 
    u.username,
    u.access_level,
    u.role,
    'regulatory_docs' as document_type,
    check_user_access(u.access_level, 'regulatory_docs') as access_type
FROM users u
WHERE u.access_level IS NOT NULL
ORDER BY u.access_level; 