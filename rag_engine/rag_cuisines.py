import os
import glob
import numpy as np

from groq import Groq

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# -------------------------------------------
# 1. Set your Groq API key
# -------------------------------------------
os.environ["GROQ_API_KEY"]
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# -------------------------------------------
# 2. Data paths
# -------------------------------------------
DATA_DIR = "data/recipes"


# -------------------------------------------
# 3. Load documents
# -------------------------------------------
def load_documents():
    docs = []
    for path in glob.glob(os.path.join(DATA_DIR, "*.txt")):
        loader = TextLoader(path, encoding="utf-8")
        docs.extend(loader.load())
    return docs


# -------------------------------------------
# 4. Build simple in-memory index (no chroma/faiss)
# -------------------------------------------
def build_index(documents):
    # For small recipes, use each full document as a single chunk
    texts = [d.page_content for d in documents]

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode(texts, normalize_embeddings=True)

    index = {
        "texts": texts,
        "embs": embeddings,
        "model": model,
    }
    return index

# def build_index(documents):
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=300,
#         chunk_overlap=50,
#         separators=["\n\n", "Ingredients:", "Steps:", "\n"]
#     )
#     chunks = splitter.split_documents(documents)

#     texts = [c.page_content for c in chunks]

#     # SentenceTransformer embeddings
#     model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
#     embeddings = model.encode(texts, normalize_embeddings=True)

#     index = {
#         "texts": texts,
#         "embs": embeddings,
#         "model": model,
#     }
#     return index


# -------------------------------------------
# 5. Retrieve top-k similar chunks
# -------------------------------------------
def retrieve_top_k(query, index, k=4):
    model = index["model"]
    texts = index["texts"]
    embs = index["embs"]  # shape: (N, d)

    q_emb = model.encode([query], normalize_embeddings=True)[0]  # shape: (d,)
    scores = np.dot(embs, q_emb)  # cosine similarity since normalized
    top_k_idx = np.argsort(scores)[-k:][::-1]

    top_chunks = [texts[i] for i in top_k_idx]
    return "\n\n".join(top_chunks)


# -------------------------------------------
# 6. Call Groq LLM
# -------------------------------------------
def call_groq_llm(prompt_text):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0
    )
    return response.choices[0].message.content


# -------------------------------------------
# 7. Main flow
# -------------------------------------------
def main():
    print("\nLoading recipe documents...")
    docs = load_documents()
    print(f"Loaded {len(docs)} files\n")

    print("Building in-memory embedding index...")
    index = build_index(docs)

    # query = "Give me the authentic recipe for Indian Chicken Curry."
    # query = "Give me the authentic recipe for Italian Pasta."
    query = "Give me the authentic recipe for Mexican Chicken Tacos."



    print("\nRetrieving top-k context chunks...\n")
    context = retrieve_top_k(query, index, k=4)

    prompt = f"""
You are an expert chef.

Using ONLY the retrieved context, return the recipe STRICTLY in this JSON:

{{
  "dish_name": "",
  "cuisine": "",
  "ingredients": [
    {{"item": "", "quantity": "", "notes": ""}}
  ],
  "steps": [],
  "cooking_time": "",
  "difficulty": "",
  "authentic_tips": []
}}

MAPPING RULES (VERY IMPORTANT):
- If the context contains a line like "Cooking Time: X", then:
  - Set "cooking_time" to the value X (for example: "15 minutes").
- If the context contains a line like "Difficulty: Y", then:
  - Set "difficulty" to the value Y (for example: "Easy").
- If the context contains a section "Authentic Tips:" with bullet points,
  - Convert each bullet into an element inside "authentic_tips"

RULES:
- Use ONLY information from the context.
- If a field is missing, set it to null or [].
- DO NOT GUESS.
- DO NOT add vague items like "salt (required amount)".

Context:
{context}

User question:
{query}
"""

    print("\nCalling Groq LLM...\n")
    result = call_groq_llm(prompt)

    print("\n======= RAG OUTPUT (GROQ) =======\n")
    print(result)
    print("\n=================================\n")


if __name__ == "__main__":
    main()
