from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


SECTION_KEYS = [
    "summary",
    "objective",
    "experience",
    "work experience",
    "projects",
    "skills",
    "technical skills",
    "education",
    "certifications",
    "awards",
    "misc",
]


class ResumeIndex:
    def __init__(
        self,
        vectorizer: TfidfVectorizer,
        matrix,
        resume_ids: List[str],
        section_texts: List[str],
        sec_map: List[Dict[str, str]],
    ):
        self.vectorizer = vectorizer
        self.matrix = matrix
        self.resume_ids = resume_ids
        self.section_texts = section_texts
        self.sec_map = sec_map  # each item: {section -> text}

    @classmethod
    def build(cls, items: List[Tuple[str, Dict]]):
        resume_ids = []
        section_texts = []
        sec_map = []
        for rid, rjson in items:
            sections = rjson.get("sections", {})
            joined = []
            local_map = {}
            for k in SECTION_KEYS:
                txt = sections.get(k, "")
                local_map[k] = txt
                if txt:
                    joined.append(f"[{k}]\n{txt}")
            resume_ids.append(rid)
            sec_map.append(local_map)
            section_texts.append("\n\n".join(joined) if joined else rjson.get("raw_text", ""))
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words="english")
        matrix = vectorizer.fit_transform(section_texts)
        return cls(vectorizer, matrix, resume_ids, section_texts, sec_map)

    def match(self, jd: str, top_k: int = 3):
        q = self.vectorizer.transform([jd])
        sims = cosine_similarity(q, self.matrix)[0]
        order = np.argsort(-sims)[:top_k]
        results = []
        for idx in order:
            rid = self.resume_ids[idx]
            score = float(sims[idx])
            # section scores
            sec_scores = {}
            for k, txt in self.sec_map[idx].items():
                if not txt:
                    sec_scores[k] = 0.0
                    continue
                s_vec = self.vectorizer.transform([f"[{k}]\n{txt}"])
                sec_scores[k] = float(cosine_similarity(q, s_vec)[0, 0])
            highlights = self._extract_highlights(jd, self.section_texts[idx])
            results.append((rid, score, highlights, sec_scores))
        return results

    def _extract_highlights(self, jd: str, resume_text: str, n: int = 6) -> List[str]:
        fea_names = self.vectorizer.get_feature_names_out()
        q_vec = self.vectorizer.transform([jd])
        d_vec = self.vectorizer.transform([resume_text])
        q_idx = q_vec.nonzero()[1]
        d_idx = d_vec.nonzero()[1]
        common = set(q_idx).intersection(set(d_idx))
        weights = [(fea, float(q_vec[0, i] + d_vec[0, i])) for i, fea in enumerate(fea_names) if i in common]
        weights.sort(key=lambda x: -x[1])
        return [w[0] for w in weights[:n]]
