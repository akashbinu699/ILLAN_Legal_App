"""Database models for the application."""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.db import Base

class Submission(Base):
    """Client form submissions."""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True)  # CAS-YYYY-XXX format
    cas_number = Column(Integer, index=True)  # CAS number assigned to email (CAS-1, CAS-2, etc.)
    email = Column(String, index=True)
    phone = Column(String)
    description = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="NEW")  # NEW, PROCESSING, REVIEWED, SENT
    stage = Column(String, default="RAPO")  # CONTROL, RAPO, LITIGATION
    
    # Generated drafts and prompts
    generated_email_draft = Column(Text, nullable=True)
    generated_appeal_draft = Column(Text, nullable=True)
    email_prompt = Column(Text, nullable=True)
    appeal_prompt = Column(Text, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="submission", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="submission", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Submission(id={self.id}, case_id={self.case_id}, email={self.email})>"

class Document(Base):
    """Processed documents from submissions."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), index=True)
    filename = Column(String)
    mime_type = Column(String)
    original_text = Column(Text)  # Raw extracted text
    cleaned_text = Column(Text)  # MarkItDown cleaned text
    structured_data = Column(JSON)  # Tables, financial data as JSON
    page_count = Column(Integer)
    processed_at = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)  # For handling amendments
    
    # Relationships
    submission = relationship("Submission", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, submission_id={self.submission_id})>"

class Chunk(Base):
    """Document chunks with embedding metadata."""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True)
    chunk_index = Column(Integer)  # Position in document
    content = Column(Text)  # Chunk text content
    page_number = Column(Integer)
    section_title = Column(String, nullable=True)
    clause_number = Column(String, nullable=True)
    embedding_id = Column(String, index=True)  # Reference to ChromaDB embedding
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"

class Query(Base):
    """Query history and responses."""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=True, index=True)  # Link to case
    query_text = Column(Text)
    response_text = Column(Text)
    citations = Column(JSON)  # List of citations with metadata
    retrieved_chunk_ids = Column(JSON)  # IDs of chunks used
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    submission = relationship("Submission", back_populates="queries")
    
    def __repr__(self):
        return f"<Query(id={self.id}, query_text={self.query_text[:50]}...)>"

