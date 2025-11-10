import os
import faiss
import numpy as np
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from unstructured.partition.auto import partition
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize model + FAISS
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
faiss_index = None
chunks_map = {}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/init_index")
def init_index():
    global faiss_index, chunks_map
    faiss_index = faiss.IndexFlatL2(384)
    chunks_map = {}
    return {"message": "FAISS index initialized."}

@app.post("/upload")
async def upload_file(file: UploadFile):
    global faiss_index, chunks_map

    os.makedirs("uploads", exist_ok=True)
    path = f"uploads/{file.filename}"

    with open(path, "wb") as f:
        f.write(await file.read())

    # Extract text from any supported format
    elements = partition(filename=path)
    text = "\n".join([el.text for el in elements if el.text])

    # Split text into manageable chunks
    chunk_size, overlap = 800, 100
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

    # Embed chunks and add to FAISS
    embeds = embedding_model.encode(chunks)
    if faiss_index is None:
        faiss_index = faiss.IndexFlatL2(embeds.shape[1])

    start = faiss_index.ntotal
    faiss_index.add(np.array(embeds))

    for i, chunk in enumerate(chunks):
        chunks_map[start + i] = chunk

    return {"message": f"Indexed {len(chunks)} chunks from {file.filename}"}

@app.post("/chat")
async def chat(query: str = Form(...)):
    global faiss_index, chunks_map
    if faiss_index is None:
        return {"error": "No data indexed yet. Upload a file first."}

    q_emb = embedding_model.encode([query])
    D, I = faiss_index.search(np.array(q_emb), k=5)
    context = "\n\n".join([chunks_map.get(i, "") for i in I[0]])

    prompt = f"""
You are a Mount Sinai Radiology assistant.
Use the provided context to answer the question.
If information is missing, say you are unsure instead of guessing.

Context:
{context}

Question:
{query}
"""

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return {"answer": response.text.strip()}
