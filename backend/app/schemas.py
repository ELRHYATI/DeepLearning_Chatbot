from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# Auth schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[UserResponse] = None

class GoogleToken(BaseModel):
    token: str

# Grammar schemas
class GrammarRequest(BaseModel):
    text: str

class GrammarCorrection(BaseModel):
    original: str
    corrected: str
    explanation: str

class GrammarResponse(BaseModel):
    original_text: str
    corrected_text: str
    corrections: List[GrammarCorrection]

# QA schemas
class QARequest(BaseModel):
    question: str
    context: Optional[str] = None

class QAResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    sources: Optional[List[str]] = None

# Reformulation schemas
class ReformulationRequest(BaseModel):
    text: str
    style: Optional[str] = "academic"  # academic, formal, simple, paraphrase, simplification

class ReformulationResponse(BaseModel):
    original_text: str
    reformulated_text: str
    changes: Optional[Dict[str, Any]] = None

# Chat schemas
class MessageCreate(BaseModel):
    content: str
    module_type: str = "general"  # grammar, qa, reformulation, general
    metadata: Optional[Dict[str, Any]] = None
    use_web_search: Optional[bool] = False  # Force web search

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    module_type: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    message_count: int = 0
    is_shared: Optional[bool] = False
    share_token: Optional[str] = None
    
    class Config:
        from_attributes = True

class ChatSessionDetail(ChatSessionResponse):
    messages: List[MessageResponse]

# Document schemas
class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    uploaded_at: datetime
    processed: bool
    
    class Config:
        from_attributes = True

# Search schemas
class SearchRequest(BaseModel):
    query: Optional[str] = None
    module_type: Optional[str] = None  # grammar, qa, reformulation, general
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    role: Optional[str] = None  # user, assistant
    limit: int = 50
    offset: int = 0

class SearchMessageResult(BaseModel):
    id: int
    session_id: int
    session_title: str
    role: str
    content: str
    module_type: str
    created_at: Optional[str]
    highlight: str

class SearchResponse(BaseModel):
    results: List[SearchMessageResult]
    total: int
    limit: int
    offset: int
    has_more: bool

class SessionSearchRequest(BaseModel):
    query: Optional[str] = None
    module_type: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    limit: int = 20
    offset: int = 0

class SessionSearchResult(BaseModel):
    id: int
    title: str
    created_at: Optional[str]
    updated_at: Optional[str]
    message_count: int
    module_counts: Dict[str, int]
    is_shared: bool

class SessionSearchResponse(BaseModel):
    results: List[SessionSearchResult]
    total: int
    limit: int
    offset: int
    has_more: bool

# Feedback schemas
class FeedbackCreate(BaseModel):
    message_id: int
    rating: int  # 1 for 👍 (positive), -1 for 👎 (negative)
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# API Key schemas
class APIKeyCreate(BaseModel):
    key_name: str
    expires_in_days: Optional[int] = None  # Optionnel: nombre de jours avant expiration

class APIKeyResponse(BaseModel):
    id: int
    key_name: str
    api_key: str  # Affichée une seule fois lors de la création
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class APIKeyListResponse(BaseModel):
    id: int
    key_name: str
    masked_key: str  # Clé masquée pour l'affichage
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Fine-tuning schemas
class FineTuningJobCreate(BaseModel):
    job_name: str
    model_type: str  # grammar, qa, reformulation
    training_data: Dict[str, Any]  # Données d'entraînement

class FineTuningJobResponse(BaseModel):
    id: int
    job_name: str
    model_type: str
    status: str
    progress: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

# Plagiarism schemas
class PlagiarismCheckRequest(BaseModel):
    text: str
    min_similarity: Optional[float] = 0.7
    exclude_document_ids: Optional[List[int]] = None

class SimilarSection(BaseModel):
    source_text: str
    reference_text: str
    similarity: float
    source_start: int
    reference_start: int

class PlagiarismMatch(BaseModel):
    document_id: int
    document_name: str
    document_owner_id: int
    similarity: float
    ngram_similarity: float
    semantic_similarity: float
    sequence_similarity: float
    similar_sections: List[SimilarSection]
    document_length: int
    uploaded_at: Optional[str] = None

class SimilarityBreakdown(BaseModel):
    ngram_similarity: float
    semantic_similarity: float
    exact_matches: int

class PlagiarismSummary(BaseModel):
    status: str  # clean, low_risk, medium_risk, high_risk
    message: str
    similarity_percentage: float
    match_count: Optional[int] = None
    documents_checked: Optional[int] = None

class PlagiarismCheckResponse(BaseModel):
    overall_similarity: float
    plagiarism_detected: bool
    matches: List[PlagiarismMatch]
    total_documents_checked: int
    similarity_breakdown: SimilarityBreakdown
    summary: PlagiarismSummary

# Suggestions schemas
class SuggestionRequest(BaseModel):
    text: str
    cursor_position: Optional[int] = None
    module_type: Optional[str] = "general"

class SuggestionResponse(BaseModel):
    type: str  # grammar, completion, reformulation, semantic
    text: str
    confidence: float
    explanation: Optional[str] = None
    replacement: Optional[str] = None  # For grammar corrections

# AI Detection schemas
class AIDetectionResponse(BaseModel):
    is_ai: bool
    ai_probability: float  # 0-1, higher = more likely AI
    confidence: float
    message: str
    details: Optional[Dict] = None

class CombinedAnalysisResponse(BaseModel):
    plagiarism: Dict
    ai_detection: AIDetectionResponse
    combined: Dict

# Interactive Learning / Correction schemas
class MessageCorrectionCreate(BaseModel):
    message_id: int
    corrected_content: str
    correction_notes: Optional[str] = None

class MessageCorrectionResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    original_content: str
    corrected_content: str
    correction_type: str
    correction_notes: Optional[str] = None
    is_used_for_learning: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LearningStatsResponse(BaseModel):
    total_corrections: int
    corrections_by_type: Dict[str, int]
    corrections_by_user: Dict[str, int]
    improvement_rate: float  # Percentage of corrections that improved responses
    most_corrected_patterns: List[Dict[str, Any]]

