-- Migration: Add access_level column to bank_documents table
-- This script safely adds the access_level column if it doesn't exist

-- Add access_level column if it doesn't exist
DO $$ 
BEGIN
    -- Check if the column exists, if not, add it
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'bank_documents' 
        AND column_name = 'access_level'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE bank_documents ADD COLUMN access_level INTEGER DEFAULT 1;
        RAISE NOTICE 'Added access_level column to bank_documents table';
    ELSE
        RAISE NOTICE 'access_level column already exists in bank_documents table';
    END IF;
END $$;

-- Add index on access_level for better query performance
CREATE INDEX IF NOT EXISTS idx_bank_documents_access_level ON bank_documents(access_level);

-- Update any existing records that don't have access_level set
UPDATE bank_documents 
SET access_level = 1 
WHERE access_level IS NULL;

-- Add comment to the column
COMMENT ON COLUMN bank_documents.access_level IS 'Access level 1-5 based on document type (1=Public, 2=Internal, 3=Confidential, 4=Restricted, 5=Executive)'; 