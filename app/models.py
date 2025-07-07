"""
Database Models
SQLAlchemy models for BankBot application.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, func, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from .database import Base
from .config import settings
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Import pgvector extension for vector operations
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback if pgvector is not installed
    from sqlalchemy import Column
    Vector = lambda dim: Column(ARRAY(Float, dimensions=dim))

class User(Base):
    """User model with access level support"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Access Level Matrix fields
    access_level = Column(Integer, nullable=False, default=1)  # 1-5 as per matrix
    role = Column(String(50), nullable=True)  # Risk Analyst, Compliance Officer, etc.
    
    # Status fields
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("BankDocument", back_populates="user")
    documents_v2 = relationship("BankDocumentV2", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class BankDocument(Base):
    """Original bank document model (legacy)"""
    __tablename__ = "bank_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Document identification
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    
    # Content (single version - legacy)
    extracted_text = Column(Text, nullable=True)
    
    # Vector embedding (single version - legacy)
    embedding = Column(ARRAY(Float), nullable=True)
    
    # Document classification
    document_type = Column(String(50), nullable=True)
    access_level = Column(Integer, nullable=True)  # Legacy field
    
    # Metadata
    document_metadata = Column(JSON, nullable=True)
    
    # Processing information
    is_processed = Column(Boolean, default=False)
    processing_date = Column(DateTime, default=datetime.utcnow)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="documents")

class BankDocumentV2(Base):
    """Access Level Matrix compliant bank document model"""
    __tablename__ = "bank_documents_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Document identification
    source_url = Column(String(500), nullable=True)
    source_filename = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)  # DocumentType enum value
    
    # Multiple content versions - ACCESS MATRIX COMPLIANCE
    content_full = Column(Text, nullable=True)
    content_summary = Column(Text, nullable=True)
    content_relevant = Column(Text, nullable=True)
    
    # Multiple embeddings for different content versions
    embedding_full = Column(ARRAY(Float), nullable=True)
    embedding_summary = Column(ARRAY(Float), nullable=True)
    embedding_relevant = Column(ARRAY(Float), nullable=True)
    
    # Chunk information
    chunk_index = Column(Integer, default=0)
    total_chunks = Column(Integer, default=1)
    
    # Metadata
    document_metadata = Column(JSON, nullable=True)
    
    # Processing information
    is_processed = Column(Boolean, default=False)
    processing_date = Column(DateTime, default=datetime.utcnow)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="documents_v2")

class AuditLog(Base):
    """Audit log model for compliance tracking"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Action details
    action = Column(String(50), nullable=False)  # query, search, document_access, etc.
    resource_type = Column(String(50), nullable=True)  # document, user, etc.
    resource_id = Column(String(255), nullable=True)
    
    # Access control info
    user_access_level = Column(Integer, nullable=True)
    document_type = Column(String(50), nullable=True)
    access_type_granted = Column(String(20), nullable=True)  # full, summary, relevant, none
    
    # Request details
    query_text = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Response details
    response_time_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    
    # Metadata
    additional_data = Column(JSON, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

# Access Level Matrix Enums (for reference)
class AccessType:
    """Access Types as defined in the matrix"""
    NONE = "none"
    SUMMARY = "summary"
    RELEVANT = "relevant"
    FULL = "full"

class DocumentType:
    """Document Types as defined in the matrix"""
    PUBLIC_PRODUCT_INFO = "public_product_info"
    INTERNAL_PROCEDURES = "internal_procedures"
    RISK_MODELS = "risk_models"
    REGULATORY_DOCS = "regulatory_docs"
    INVESTIGATION_REPORTS = "investigation_reports"
    EXECUTIVE_REPORTS = "executive_reports"

class UserAccessLevel:
    """User Access Levels as defined in the matrix"""
    PUBLIC = 1
    INTERNAL = 2
    CONFIDENTIAL = 3
    RESTRICTED = 4
    EXECUTIVE = 5

# Access Level Matrix Implementation
ACCESS_MATRIX = {
    "Public Product Info": {
        UserAccessLevel.PUBLIC: AccessType.FULL,
        UserAccessLevel.INTERNAL: AccessType.FULL,
        UserAccessLevel.CONFIDENTIAL: AccessType.FULL,
        UserAccessLevel.RESTRICTED: AccessType.FULL,
        UserAccessLevel.EXECUTIVE: AccessType.FULL,
    },
    "Internal Procedures": {
        UserAccessLevel.PUBLIC: AccessType.NONE,
        UserAccessLevel.INTERNAL: AccessType.FULL,
        UserAccessLevel.CONFIDENTIAL: AccessType.FULL,
        UserAccessLevel.RESTRICTED: AccessType.FULL,
        UserAccessLevel.EXECUTIVE: AccessType.FULL,
    },
    "Risk Models": {
        UserAccessLevel.PUBLIC: AccessType.NONE,
        UserAccessLevel.INTERNAL: AccessType.NONE,
        UserAccessLevel.CONFIDENTIAL: AccessType.FULL,
        UserAccessLevel.RESTRICTED: AccessType.SUMMARY,
        UserAccessLevel.EXECUTIVE: AccessType.FULL,
    },
    "Regulatory Docs": {
        UserAccessLevel.PUBLIC: AccessType.NONE,
        UserAccessLevel.INTERNAL: AccessType.SUMMARY,
        UserAccessLevel.CONFIDENTIAL: AccessType.RELEVANT,
        UserAccessLevel.RESTRICTED: AccessType.FULL,
        UserAccessLevel.EXECUTIVE: AccessType.FULL,
    },
    "Investigation Reports": {
        UserAccessLevel.PUBLIC: AccessType.NONE,
        UserAccessLevel.INTERNAL: AccessType.NONE,
        UserAccessLevel.CONFIDENTIAL: AccessType.NONE,
        UserAccessLevel.RESTRICTED: AccessType.NONE,
        UserAccessLevel.EXECUTIVE: AccessType.FULL,
    },
    "Executive Reports": {
        UserAccessLevel.PUBLIC: AccessType.NONE,
        UserAccessLevel.INTERNAL: AccessType.NONE,
        UserAccessLevel.CONFIDENTIAL: AccessType.NONE,
        UserAccessLevel.RESTRICTED: AccessType.SUMMARY,
        UserAccessLevel.EXECUTIVE: AccessType.FULL,
    }
}

def check_user_access(user_level: int, document_type: str) -> str:
    """Check what access type user has for document type"""
    return ACCESS_MATRIX.get(document_type, {}).get(user_level, AccessType.NONE)

def get_content_by_access_type(document: BankDocumentV2, access_type: str) -> Optional[str]:
    """Get content based on access type"""
    if access_type == AccessType.FULL:
        return document.content_full
    elif access_type == AccessType.SUMMARY:
        return document.content_summary
    elif access_type == AccessType.RELEVANT:
        return document.content_relevant
    else:  # AccessType.NONE
        return None

def get_embedding_by_access_type(document: BankDocumentV2, access_type: str) -> Optional[List[float]]:
    """Get embedding based on access type"""
    if access_type == AccessType.FULL:
        return document.embedding_full
    elif access_type == AccessType.SUMMARY:
        return document.embedding_summary
    elif access_type == AccessType.RELEVANT:
        return document.embedding_relevant
    else:  # AccessType.NONE
        return None

# ------------------------------------------------------------------------------
# Pydantic Schemas for Authentication & JWT
# ------------------------------------------------------------------------------
class Token(BaseModel):
    """Schema for JWT access token response"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Internal token payload schema (decoded JWT data)"""
    user_id: str
    username: str
    access_level: int
    role: Optional[str] = None

# ---------------------------------------
# Conversation & Query History Models
# ---------------------------------------

class QueryHistory(Base):
    """Stores each user query and corresponding response for session history."""
    __tablename__ = "query_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Relationship to user that issued the query
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Logical conversation/session identifier – can group many QueryHistory rows
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Route that produced this entry -> retrieve | answer
    route = Column(String(20), nullable=False)

    # Original user query text
    query_text = Column(Text, nullable=False)

    # Raw text returned to the user (chunks JSON or answer text)
    response_text = Column(Text, nullable=True)

    # Request metadata
    ip_address = Column(String(45), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")

# --------------------------------------- 