# from pathlib import Path
# from typing import Dict, Any, Optional, List, Tuple
# import orjson
# import pickle

# # ---------------- PATH SETUP ----------------
# DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# DATA_DIR.mkdir(parents=True, exist_ok=True)
# RESUMES_JSON = DATA_DIR / "resumes.json"
# INDEX_PKL = DATA_DIR / "index.pkl"


# # ---------------- JSON STORE ----------------
# def _load_json() -> Dict[str, Any]:
#     if RESUMES_JSON.exists():
#         return orjson.loads(RESUMES_JSON.read_bytes())
#     return {}


# def _dump_json(obj: Dict[str, Any]):
#     RESUMES_JSON.write_bytes(orjson.dumps(obj))


# def put_resume(resume_id: str, json_obj: Dict[str, Any]):
#     db = _load_json()
#     db[resume_id] = json_obj
#     _dump_json(db)


# def get_resume(resume_id: str) -> Optional[Dict[str, Any]]:
#     db = _load_json()
#     return db.get(resume_id)


# # def list_resumes(ids: Optional[List[str]] = None) -> List[Tuple[str, Dict[str, Any]]]:
# #     db = _load_json()
# #     items = list(db.items())
# #     if ids:
# #         items = [(i, db[i]) for i in ids if i in db]
# #     return items


# # def list_resumes(resume_ids):
# #     data = []
# #     for rid in resume_ids:
# #         content = load_json(rid)
# #         data.append((rid, content))  # return tuple (id, json)
# #     return data


# def list_resumes(resume_ids):
#     items = []
#     for rid in resume_ids:
#         data = load_json(rid)
#         items.append((rid, data))   # ✅ we return tuple (id, json)
#     return items


# # ---------------- INDEX STORE (TF-IDF) ----------------
# def save_index(obj):
#     with open(INDEX_PKL, "wb") as f:
#         pickle.dump(obj, f)


# def load_index():
#     if INDEX_PKL.exists():
#         with open(INDEX_PKL, "rb") as f:
#             return pickle.load(f)
#     return None




import json
from pathlib import Path
import pickle

# Root data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Subfolders
RESUME_DIR = DATA_DIR / "resumes"
RESUME_DIR.mkdir(parents=True, exist_ok=True)

INDEX_PKL = DATA_DIR / "resume_index.pkl"

# -------------------- Resume Save / Load --------------------
def put_resume(resume_id: str, content: dict):
    """Save one resume JSON to a file"""
    file_path = RESUME_DIR / f"{resume_id}.json"
    with open(file_path, "w") as f:
        json.dump(content, f)

def get_resume(resume_id: str) -> dict:
    """Load one resume JSON from a file"""
    file_path = RESUME_DIR / f"{resume_id}.json"
    if file_path.exists():
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def list_resumes(resume_ids: list[str]) -> list[tuple[str, dict]]:
    """Return list of (resume_id, resume_content) tuples"""
    results = []
    for rid in resume_ids:
        file_path = RESUME_DIR / f"{rid}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
                results.append((rid, data))  # exactly two values: (id, data)
    return results

# -------------------- Index Save / Load --------------------
def save_index(index_obj):
    """Save learned vector index"""
    with open(INDEX_PKL, "wb") as f:
        pickle.dump(index_obj, f)

def load_index():
    """Load learned vector index"""
    if INDEX_PKL.exists():
        with open(INDEX_PKL, "rb") as f:
            return pickle.load(f)
    return None
