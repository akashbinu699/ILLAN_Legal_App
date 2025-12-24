"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Submission Schemas
class AttachedFileSchema(BaseModel):
    name: str
    mimeType: str
    base64: str

class SubmissionCreate(BaseModel):
    email: EmailStr
    phone: str
    description: str
    files: List[AttachedFileSchema]

class SubmissionResponse(BaseModel):
    id: int
    case_id: str
    email: str
    phone: str
    description: str
    submitted_at: datetime
    status: str
    stage: str
    generated_email_draft: Optional[str] = None
    generated_appeal_draft: Optional[str] = None
    email_prompt: Optional[str] = None
    appeal_prompt: Optional[str] = None
    
    class Config:
        from_attributes = True

# Query Schemas
class QueryRequest(BaseModel):
    query: str
    case_id: Optional[str] = None  # Optional: filter by specific case

class Citation(BaseModel):
    document_id: int
    page_number: int
    section_title: Optional[str] = None
    clause_number: Optional[str] = None
    chunk_id: int

class QueryResponse(BaseModel):
    response: str
    citations: List[Citation]
    retrieved_chunks: int
    query_id: int

# Case Schemas
class PrestationSchema(BaseModel):
    name: str
    isAccepted: bool

class CaseResponse(BaseModel):
    id: int
    case_id: str
    email: str
    phone: str
    description: str
    submitted_at: datetime
    status: str
    stage: str
    prestations: List[PrestationSchema] = []
    generatedEmailDraft: Optional[str] = None
    generatedAppealDraft: Optional[str] = None
    emailPrompt: Optional[str] = None
    appealPrompt: Optional[str] = None
    
    class Config:
        from_attributes = True

class CaseUpdate(BaseModel):
    generatedEmailDraft: Optional[str] = None
    generatedAppealDraft: Optional[str] = None
    emailPrompt: Optional[str] = None
    appealPrompt: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None

class QueryHistoryResponse(BaseModel):
    id: int
    query_text: str
    response_text: str
    citations: List[Citation]
    retrieved_chunk_ids: Optional[List] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class GenerateDraftRequest(BaseModel):
    prompt: str
    draft_type: str  # 'email' or 'appeal'

class GenerateDraftResponse(BaseModel):
    draft: str
    prompt: str

class StageDetectionRequest(BaseModel):
    description: str
    files: List[AttachedFileSchema] = []

class PrestationSchema(BaseModel):
    name: str
    isAccepted: bool

class StageDetectionResponse(BaseModel):
    stage: str
    prestations: List[PrestationSchema]

class EmailGroupResponse(BaseModel):
    email: str
    cases: List[CaseResponse]

