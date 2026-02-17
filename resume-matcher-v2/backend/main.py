# # from fastapi import FastAPI, UploadFile, File, HTTPException
# # from fastapi.responses import JSONResponse
# # from typing import List
# # from pathlib import Path
# # from .schemas import UploadResponse, LearnRequest, LearnResponse, MatchRequest, MatchResponse, CandidateScore
# # from .utils import new_resume_id
# # from .parsers import parse_file_to_json
# # from .storage import put_resume, list_resumes, save_index, load_index, DATA_DIR, INDEX_PKL
# # from .nlp import ResumeIndex

# # app = FastAPI(title="Resume Matcher v2", version="0.1.0")

# # UPLOAD_TMP = DATA_DIR / "uploads"
# # UPLOAD_TMP.mkdir(parents=True, exist_ok=True)

# # # -------------------- UPLOAD --------------------
# # @app.post("/upload", response_model=UploadResponse)
# # def upload_resumes(files: List[UploadFile] = File(..., description="Upload up to 3 resumes (.pdf/.docx/.txt)")):
# #     if not files or len(files) == 0:
# #         raise HTTPException(400, "No files provided")
# #     if len(files) > 3:
# #         raise HTTPException(400, "Provide at most 3 files per request")
# #     ids = []
# #     for f in files:
# #         suffix = Path(f.filename).suffix.lower()
# #         if suffix not in (".pdf", ".docx", ".txt"):
# #             raise HTTPException(400, f"Unsupported type: {suffix}")
# #         rid = new_resume_id()
# #         temp = UPLOAD_TMP / f"{rid}{suffix}"
# #         with temp.open("wb") as out:
# #             out.write(f.file.read())
# #         try:
# #             j = parse_file_to_json(temp)
# #         except Exception as e:
# #             raise HTTPException(422, f"Failed to parse {f.filename}: {e}")
# #         put_resume(rid, j)
# #         ids.append(rid)
# #     return UploadResponse(resume_ids=ids)

# # # -------------------- LEARN --------------------
# # @app.post("/learn", response_model=LearnResponse)
# # def learn(req: LearnRequest):
# #     items = list_resumes(req.resume_ids)
# #     if not items:
# #         raise HTTPException(400, "No resumes found to learn")
# #     index = ResumeIndex.build(items)
# #     save_index(index)
# #     return LearnResponse(learned_count=len(items), vectorizer_path=str(INDEX_PKL))

# # # -------------------- MATCH --------------------
# # @app.post("/match", response_model=MatchResponse)
# # def match(req: MatchRequest):
# #     index = load_index()
# #     if index is None:
# #         raise HTTPException(400, "Index not found. Call /learn after /upload.")
# #     raw = index.match(req.job_description, top_k=req.top_k)
# #     results = []
# #     for rid, score, highlights, sec_scores in raw:
# #         results.append(
# #             CandidateScore(
# #                 resume_id=rid,
# #                 score=round(score, 4),
# #                 highlights=highlights,
# #                 section_scores={k: round(v, 4) for k, v in sec_scores.items() if v > 0}
# #             )
# #         )
# #     return MatchResponse(
# #         role=req.job_description[:80] + ("..." if len(req.job_description) > 80 else ""),
# #         results=results
# #     )







# from fastapi import FastAPI, UploadFile, File, HTTPException
# from typing import List
# from pathlib import Path

# from .schemas import (
#     UploadResponse,
#     LearnRequest,
#     LearnResponse,
#     MatchRequest,
#     MatchResponse,
#     CandidateScore,
# )
# from .utils import new_resume_id
# from .parsers import parse_file_to_json
# from .storage import save_index, load_index, DATA_DIR, INDEX_PKL
# from .nlp import ResumeIndex
# from .database import SessionLocal, Resume, MatchResult, init_db

# app = FastAPI(title="Resume Matcher v2", version="1.0.0")

# # Init DB tables
# init_db()

# UPLOAD_TMP = DATA_DIR / "uploads"
# UPLOAD_TMP.mkdir(parents=True, exist_ok=True)


# # ---------- POST: /upload (3 resumes → DB) ----------
# @app.post("/upload", response_model=UploadResponse)
# def upload_resumes(files: List[UploadFile] = File(..., description="Upload up to 3 resumes (.pdf/.docx/.txt)")):
#     if not files:
#         raise HTTPException(status_code=400, detail="No files provided")
#     if len(files) > 3:
#         raise HTTPException(status_code=400, detail="Provide at most 3 files per request")

#     session = SessionLocal()
#     resume_ids: List[str] = []

#     try:
#         for f in files:
#             suffix = Path(f.filename).suffix.lower()
#             if suffix not in (".pdf", ".docx", ".txt"):
#                 raise HTTPException(status_code=400, detail=f"Unsupported type: {suffix}")

#             rid = new_resume_id()
#             temp_path = UPLOAD_TMP / f"{rid}{suffix}"

#             with temp_path.open("wb") as out:
#                 out.write(f.file.read())

#             try:
#                 parsed = parse_file_to_json(temp_path)
#             except Exception as e:
#                 raise HTTPException(status_code=422, detail=f"Failed to parse {f.filename}: {e}")

#             db_resume = Resume(
#                 resume_id=rid,
#                 filename=f.filename,
#                 content_json=parsed
#             )
#             session.add(db_resume)
#             resume_ids.append(rid)

#         session.commit()
#         return UploadResponse(resume_ids=resume_ids)

#     finally:
#         session.close()


# # ---------- POST: /learn (build index from DB) ----------
# @app.post("/learn", response_model=LearnResponse)
# def learn(req: LearnRequest):
#     if not req.resume_ids:
#         raise HTTPException(status_code=400, detail="No resume_ids provided")

#     session = SessionLocal()
#     try:
#         db_resumes = (
#             session.query(Resume)
#             .filter(Resume.resume_id.in_(req.resume_ids))
#             .all()
#         )
#         if not db_resumes:
#             raise HTTPException(status_code=400, detail="No resumes found to learn")

#         # {resume_id: parsed_json}
#         items = {r.resume_id: r.content_json for r in db_resumes}

#         index = ResumeIndex.build(items)
#         save_index(index)

#         return LearnResponse(
#             learned_count=len(items),
#             vectorizer_path=str(INDEX_PKL),
#         )
#     finally:
#         session.close()


# # ---------- POST: /match (JD vs 3 resumes → score, fit, desc order) ----------
# @app.post("/match", response_model=MatchResponse)
# def match(req: MatchRequest):
#     index = load_index()
#     if index is None:
#         raise HTTPException(status_code=400, detail="Index not found. Call /learn after /upload.")

#     raw = index.match(req.job_description, top_k=req.top_k)

#     if not raw:
#         return MatchResponse(role=req.job_description[:80], results=[])

#     session = SessionLocal()
#     results: List[CandidateScore] = []

#     try:
#         for rid, score, highlights, sec_scores in raw:
#             skills_score = float(sec_scores.get("skills", 0.0)) if isinstance(sec_scores, dict) else 0.0
#             experience_score = float(sec_scores.get("experience", 0.0)) if isinstance(sec_scores, dict) else 0.0
#             education_score = float(sec_scores.get("education", 0.0)) if isinstance(sec_scores, dict) else 0.0

#             # JD + resume relevance → fit label
#             if score >= 0.8:
#                 fit_label = "Excellent"
#             elif score >= 0.6:
#                 fit_label = "Good"
#             elif score >= 0.4:
#                 fit_label = "Average"
#             else:
#                 fit_label = "Low"

#             # Save to DB (for audit / GET)
#             db_match = MatchResult(
#                 job_description=req.job_description,
#                 resume_id=rid,
#                 score=float(score),
#                 skills_score=skills_score,
#                 experience_score=experience_score,
#                 education_score=education_score,
#                 fit_label=fit_label,
#             )
#             session.add(db_match)

#             results.append(
#                 CandidateScore(
#                     resume_id=rid,
#                     score=round(float(score), 4),
#                     fit=fit_label,
#                     skills_score=round(skills_score, 4) if skills_score else None,
#                     experience_score=round(experience_score, 4) if experience_score else None,
#                     education_score=round(education_score, 4) if education_score else None,
#                     justification=highlights or [],
#                 )
#             )

#         session.commit()

#     finally:
#         session.close()

#     # Descending order (best match → lowest)
#     results_sorted = sorted(results, key=lambda r: r.score, reverse=True)

#     role = req.job_description[:80]
#     if len(req.job_description) > 80:
#         role += "..."

#     return MatchResponse(role=role, results=results_sorted)


# # ---------- GET: /resumes (see stored resumes) ----------
# @app.get("/resumes")
# def get_resumes():
#     session = SessionLocal()
#     try:
#         db_resumes = session.query(Resume).all()
#         if not db_resumes:
#             raise HTTPException(status_code=404, detail="No resumes found")
#         return {
#             "resumes": [
#                 {"resume_id": r.resume_id, "filename": r.filename}
#                 for r in db_resumes
#             ]
#         }
#     finally:
#         session.close()


# # ---------- GET: /match (see all match results from DB) ----------
# @app.get("/match")
# def get_match_results():
#     session = SessionLocal()
#     try:
#         db_results = (
#             session.query(MatchResult)
#             .order_by(MatchResult.score.desc())
#             .all()
#         )
#         if not db_results:
#             raise HTTPException(status_code=404, detail="No match results found")

#         return {
#             "results": [
#                 {
#                     "resume_id": r.resume_id,
#                     "score": round(float(r.score), 4),
#                     "fit": r.fit_label,
#                     "skills_score": r.skills_score,
#                     "experience_score": r.experience_score,
#                     "education_score": r.education_score,
#                 }
#                 for r in db_results
#             ]
#         }
#     finally:
#         session.close()





# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.responses import JSONResponse
# from typing import List
# from pathlib import Path

# from .schemas import (
#     UploadResponse,
#     LearnRequest,
#     LearnResponse,
#     MatchRequest,
#     MatchResponse,
#     CandidateScore,
# )
# from .utils import new_resume_id
# from .parsers import parse_file_to_json
# from .storage import save_index, load_index, DATA_DIR, INDEX_PKL
# from .nlp import ResumeIndex
# from .database import SessionLocal, Resume, MatchResult, init_db

# app = FastAPI(title="Resume Matcher v2", version="0.1.0")

# # Initialize database
# init_db()

# # -------------------- UPLOAD --------------------
# @app.post("/upload", response_model=UploadResponse)
# def upload_resumes(files: List[UploadFile] = File(...)):
#     if not files or len(files) == 0:
#         raise HTTPException(400, "No files provided")
#     if len(files) > 3:
#         raise HTTPException(400, "Provide at most 3 files per request")

#     db = SessionLocal()
#     ids = []

#     for f in files:
#         suffix = Path(f.filename).suffix.lower()
#         if suffix not in (".pdf", ".docx", ".txt"):
#             raise HTTPException(400, f"Unsupported file type: {suffix}")

#         rid = new_resume_id()
#         temp_path = DATA_DIR / f"{rid}{suffix}"

#         # Save uploaded file temporarily
#         with temp_path.open("wb") as out:
#             out.write(f.file.read())

#         try:
#             resume_json = parse_file_to_json(temp_path)
#         except Exception as e:
#             raise HTTPException(422, f"Failed to parse {f.filename}: {e}")

#         # Save parsed resume data to DB
#         new_resume = Resume(
#             resume_id=rid,
#             filename=f.filename,
#             content_json=resume_json,
#         )
#         db.add(new_resume)
#         ids.append(rid)

#     db.commit()
#     db.close()

#     return UploadResponse(resume_ids=ids)

# # -------------------- LEARN --------------------
# @app.post("/learn", response_model=LearnResponse)
# def learn(req: LearnRequest):
#     db = SessionLocal()
#     items = []
#     for rid in req.resume_ids:
#         resume = db.query(Resume).filter(Resume.resume_id == rid).first()
#         if resume:
#             items.append((rid, resume.content_json))
#     db.close()

#     if not items:
#         raise HTTPException(400, "No resumes found to learn")

#     # Build index (vectorizer)
#     index = ResumeIndex.build(items)
#     save_index(index)
#     return LearnResponse(learned_count=len(items), vectorizer_path=str(INDEX_PKL))

# # -------------------- MATCH --------------------
# @app.post("/match", response_model=MatchResponse)
# def match(req: MatchRequest):
#     index = load_index()
#     if index is None:
#         raise HTTPException(400, "No index found. Run /learn first.")

#     # Perform matching
#     raw_results = index.match(req.job_description, top_k=req.top_k)
#     results = []
#     db = SessionLocal()

#     for rid, score, highlights, sec_scores in raw_results:
#         candidate_score = CandidateScore(
#             resume_id=rid,
#             score=round(score, 4),
#             highlights=highlights,
#             section_scores={k: round(v, 4) for k, v in sec_scores.items() if v > 0},
#         )
#         results.append(candidate_score)

#         # Save results to DB
#         match_entry = MatchResult(
#             job_description=req.job_description[:200],
#             resume_id=rid,
#             score=round(score, 4),
#             skills_score=sec_scores.get("skills", 0.0),
#             experience_score=sec_scores.get("experience", 0.0),
#             education_score=sec_scores.get("education", 0.0),
#             fit_label="Best Fit" if score > 0.75 else "Average Fit",
#         )
#         db.add(match_entry)

#     db.commit()
#     db.close()

#     return MatchResponse(
#         role=req.job_description[:80] + ("..." if len(req.job_description) > 80 else ""),
#         results=results,
#     )

# # -------------------- GET RESUMES (For Testing) --------------------
# @app.get("/resumes")
# def get_all_resumes():
#     db = SessionLocal()
#     resumes = db.query(Resume).all()
#     db.close()
#     return [{"resume_id": r.resume_id, "filename": r.filename} for r in resumes]







from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
from pathlib import Path

from .schemas import (
    UploadResponse,
    LearnRequest,
    LearnResponse,
    MatchRequest,
    MatchResponse,
    CandidateScore,
)
from .utils import new_resume_id
from .parsers import parse_file_to_json
from .storage import save_index, load_index, DATA_DIR, INDEX_PKL
from .nlp import ResumeIndex
from .database import SessionLocal, Resume, MatchResult, init_db

app = FastAPI(title="Resume Matcher v2", version="0.1.0")

# Initialize database
init_db()

# -------------------- UPLOAD --------------------
@app.post("/upload", response_model=UploadResponse)
def upload_resumes(files: List[UploadFile] = File(...)):
    if not files or len(files) == 0:
        raise HTTPException(400, "No files provided")
    if len(files) > 3:
        raise HTTPException(400, "Provide at most 3 files per request")

    db = SessionLocal()
    ids = []

    for f in files:
        suffix = Path(f.filename).suffix.lower()
        if suffix not in (".pdf", ".docx", ".txt"):
            raise HTTPException(400, f"Unsupported file type: {suffix}")

        rid = new_resume_id()
        temp_path = DATA_DIR / f"{rid}{suffix}"

        # Save uploaded file temporarily
        with temp_path.open("wb") as out:
            out.write(f.file.read())

        try:
            resume_json = parse_file_to_json(temp_path)
        except Exception as e:
            raise HTTPException(422, f"Failed to parse {f.filename}: {e}")

        # Save parsed resume data to DB
        new_resume = Resume(
            resume_id=rid,
            filename=f.filename,
            content_json=resume_json,
        )
        db.add(new_resume)
        ids.append(rid)

    db.commit()
    db.close()

    return UploadResponse(resume_ids=ids)

# -------------------- LEARN --------------------
@app.post("/learn", response_model=LearnResponse)
def learn(req: LearnRequest):
    db = SessionLocal()
    items = []
    for rid in req.resume_ids:
        resume = db.query(Resume).filter(Resume.resume_id == rid).first()
        if resume:
            items.append((rid, resume.content_json))
    db.close()

    if not items:
        raise HTTPException(400, "No resumes found to learn")

    # Build index (vectorizer)
    index = ResumeIndex.build(items)
    save_index(index)
    return LearnResponse(learned_count=len(items), vectorizer_path=str(INDEX_PKL))

# -------------------- MATCH --------------------
@app.post("/match", response_model=MatchResponse)
def match(req: MatchRequest):
    index = load_index()
    if index is None:
        raise HTTPException(400, "No index found. Run /learn first.")
    if len(req.job_description.strip().split()) < 5:
        raise HTTPException(400, "please provide a valid job description (not a random sentence).")
    
    db = SessionLocal()
    raw_results = index.match(req.job_description, top_k=req.top_k)
    results = []

    for rid, score, highlights, sec_scores in raw_results:
        # ✅ Get filename from DB
        resume_record = db.query(Resume).filter(Resume.resume_id == rid).first()
        filename = resume_record.filename if resume_record else f"Resume_{rid}"

        # ✅ Build response per candidate
        candidate_score = {
            "resume_id": rid,
            "filename": filename,
            "score": round(score, 4),
            "highlights": highlights,
            "section_scores": {k: round(v, 4) for k, v in sec_scores.items() if v > 0},
        }
        results.append(candidate_score)

        # ✅ Save match result in DB
        match_entry = MatchResult(
            job_description=req.job_description[:200],
            resume_id=rid,
            score=round(score, 4),
            skills_score=sec_scores.get("skills", 0.0),
            experience_score=sec_scores.get("experience", 0.0),
            education_score=sec_scores.get("education", 0.0),
            fit_label="Best Fit" if score > 0.75 else "Average Fit",
        )
        db.add(match_entry)

    db.commit()
    db.close()

    return MatchResponse(
        role=req.job_description[:80] + ("..." if len(req.job_description) > 80 else ""),
        results=results,
    )

# -------------------- GET RESUMES (For Testing) --------------------
@app.get("/resumes")
def get_all_resumes():
    db = SessionLocal()
    resumes = db.query(Resume).all()
    db.close()
    return [{"resume_id": r.resume_id, "filename": r.filename} for r in resumes]

