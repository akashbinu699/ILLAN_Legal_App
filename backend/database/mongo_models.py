from typing import Annotated, Any, List, Optional, Dict
from pydantic import BaseModel, Field, BeforeValidator
from datetime import datetime
from bson import ObjectId

# Custom ObjectId type for Pydantic v2
# Handles conversion from string to ObjectId and vice versa
PyObjectId = Annotated[str, BeforeValidator(str)]

class MongoBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ChunkModel(MongoBaseModel):
    chunk_index: int
    content: str
    page_number: int
    section_title: Optional[str] = None
    clause_number: Optional[str] = None
    embedding_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentModel(MongoBaseModel):
    filename: str
    mime_type: str
    original_text: str = ""
    cleaned_text: str = ""
    structured_data: Dict[str, Any] = {}
    page_count: int = 0
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    chunks: List[ChunkModel] = []

class SubmissionModel(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    case_id: str
    cas_number: Optional[int] = None
    email: str
    phone: str
    description: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "NEW"
    stage: str = "RAPO"
    
    # Generated generated content
    generated_email_draft: Optional[str] = None
    generated_appeal_draft: Optional[str] = None
    email_prompt: Optional[str] = None
    appeal_prompt: Optional[str] = None
    
    # Embedded Document (1 submission = 1 document in your logic)
    document: Optional[DocumentModel] = None

class QueryModel(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    submission_id: Optional[str] = None # Reference to primary submission ID
    submission_ids: Optional[List[str]] = None
    query_text: str
    response_text: str
    citations: List[Dict[str, Any]] = []
    retrieved_chunk_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
