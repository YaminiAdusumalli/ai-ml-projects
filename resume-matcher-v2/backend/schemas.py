# from pydantic import BaseModel, Field
# from typing import List, Dict, Optional


# class UploadResponse(BaseModel):
#     resume_ids: List[str]


# class LearnRequest(BaseModel):
#     resume_ids: Optional[List[str]] = None  # if None, learn all in store


# class LearnResponse(BaseModel):
#     learned_count: int
#     vectorizer_path: str


# class MatchRequest(BaseModel):
#     job_description: str = Field(..., min_length=40)
#     top_k: int = 3


# class CandidateScore(BaseModel):
#     resume_id: str
#     score: float
#     highlights: List[str]
#     section_scores: Dict[str, float]


# class MatchResponse(BaseModel):
#     role: str
#     results: List[CandidateScore]



from pydantic import BaseModel
from typing import List, Dict, Optional

# -------------------- UPLOAD --------------------
class UploadResponse(BaseModel):
    resume_ids: List[str]

# -------------------- LEARN --------------------
class LearnRequest(BaseModel):
    resume_ids: List[str]

class LearnResponse(BaseModel):
    learned_count: int
    vectorizer_path: str

# -------------------- MATCH --------------------
class MatchRequest(BaseModel):
    resume_ids: List[str]                     # ✅ Added this line
    job_description: str
    top_k: Optional[int] = 3                  # Optional parameter, default = 3

class CandidateScore(BaseModel):
    resume_id: str
    score: float
    highlights: Optional[List[str]] = []
    section_scores: Optional[Dict[str, float]] = {}

class MatchResponse(BaseModel):
    role: str
    results: List[CandidateScore]

