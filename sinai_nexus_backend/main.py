import os
import json
import numpy as np
import google.generativeai as genai
import pdfplumber
import pandas as pd
from io import StringIO, BytesIO


from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from unstructured.partition.auto import partition
from uuid import uuid4

from huggingface_hub import InferenceClient                 # NEW

from supabase import create_client
from src.query_router import answer_scheduling_query


# ============================================================
# ENV + Supabase Client
# ============================================================
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

HF_TOKEN = os.getenv("HF_TOKEN")
hf_client = InferenceClient(provider="hf-inference", api_key=HF_TOKEN)

# ============================================================
# Gemini Config
# ============================================================
if os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
else:
    genai.configure()


# ============================================================
# Embedding API Wrapper
# ============================================================
def embed_text_list(text_list):
    """
    Uses HuggingFace Inference API to embed a list of text chunks.
    Returns a list of embedding vectors.
    """

    # API expects similarity-like call — the trick is we do 1-by-1
    embeddings = []
    for chunk in text_list:
        try:
            out = hf_client.feature_extraction(
                inputs=chunk,
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
            embeddings.append(out)
        except Exception as e:
            print("Embedding error:", e)
            embeddings.append([0.0] * 384)  # fallback vector

    return embeddings


# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(title="Sinai Nexus Backend (Supabase RAG)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class ProcessCSVRequest(BaseModel):
    csv_path: str   # full supabase path, e.g. "epic-scheduling/Locations_Rooms/schedule.csv"


@app.post("/process-locations-csv")
async def process_locations_csv(req: ProcessCSVRequest):

    full = req.csv_path.strip()

    if "/" not in full:
        return {"error": "Invalid path"}

    # bucket + path
    bucket, path = full.split("/", 1)

    try:
        # -------------------------------------------------------------
        # 1. Download CSV file
        # -------------------------------------------------------------
        response = supabase.storage.from_(bucket).download(path)
        if not response:
            return {"error": "Could not download CSV from Supabase"}

        csv_string = response.decode("latin-1")
        df = pd.read_csv(StringIO(csv_string))

        # -------------------------------------------------------------
        # 2. Rename columns
        # -------------------------------------------------------------
        df = df.rename(columns={
            "Procedure Name": "EAP Name",
            "Visit Type Name": "Visit Type Name",
            "Visit Type Length": "Visit Type Length",
            "Department Name": "DEP Name",
            "Resource Name": "Room Name"
        })

        # -------------------------------------------------------------
        # 3. Explode lists
        # -------------------------------------------------------------
        df["DEP Name"] = df["DEP Name"].astype(str).str.split("\n")
        df["Room Name"] = df["Room Name"].astype(str).str.split("\n")
        df = df.explode("DEP Name").explode("Room Name").reset_index(drop=True)

        df["DEP Name"] = df["DEP Name"].str.strip()
        df["Room Name"] = df["Room Name"].str.strip()

        # -------------------------------------------------------------
        # 4. Select columns
        # -------------------------------------------------------------
        df = df[[
            "EAP Name",
            "Visit Type Name",
            "Visit Type Length",
            "DEP Name",
            "Room Name"
        ]]

        # -------------------------------------------------------------
        # 5. Convert to parquet
        # -------------------------------------------------------------
        buffer = BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)

        parquet_name = path.split("/")[-1].replace(".csv", "_clean.parquet")
        parquet_path = f"Locations_Rooms/{parquet_name}"

        # -------------------------------------------------------------
        # 6. Upload parquet
        # -------------------------------------------------------------
        upload_response = supabase.storage.from_(bucket).upload(
            parquet_path,
            buffer.getvalue(),
            file_options={"content-type": "application/vnd.apache.parquet"}
        )

        return {
            "message": "Parquet generated and uploaded successfully",
            "parquet_path": f"{bucket}/{parquet_path}"
        }

    except Exception as e:
        return {"error": str(e)}


class AgentChatRequest(BaseModel):
    question: str


# ============================================================
# 1️⃣ SCHEDULING AGENT
# ============================================================
@app.post("/agent-chat")
def agent_chat(payload: AgentChatRequest):
    try:
        answer = answer_scheduling_query(payload.question)
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}


# ============================================================
# 2️⃣ UPLOAD → PARSE → CHUNK → EMBED → SUPABASE
# ============================================================
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    priority: int = Form(3),
    path: str = Form(...)
):
    os.makedirs("uploads", exist_ok=True)

    local_path = f"uploads/{uuid4()}_{file.filename}"

    # Save temp file
    with open(local_path, "wb") as f:
        f.write(await file.read())

    # Handle JSON notes
    if file.content_type == "application/json":
        priority = 1
        with open(local_path, "r") as f:
            data = json.load(f)
        text = data.get("content", "")
        chunks = [text] if text else []

    else:
        # Parse PDF manually (more reliable)
        if file.filename.lower().endswith(".pdf"):
            elements = []
            with pdfplumber.open(local_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        elements.append(extracted)
            text = "\n".join(elements)

        else:
            # fallback for docx, txt, md, etc.
            elements = partition(filename=local_path, strategy="text")
            text = "\n".join([el.text for el in elements if el.text])

        # Chunking
        chunk_size = 600
        overlap = 80
        chunks = [
            text[i:i + chunk_size]
            for i in range(0, len(text), chunk_size - overlap)
        ]

    # EMBEDDINGS USING HF API (NEW)
    embeddings = embed_text_list(chunks)

    # Store in DB
    rows = []
    for chunk, emb in zip(chunks, embeddings):
        rows.append({
            "content": chunk,
            "embedding": emb,
            "priority": priority,
            "file_path": path
        })

    if rows:
        supabase.table("documents").insert(rows).execute()

    return {
        "message": f"Inserted {len(chunks)} chunks",
        "chunks_added": len(chunks),
        "stored_path": path
    }


# ============================================================
# 3️⃣ DELETE FILE
# ============================================================
class DeleteRequest(BaseModel):
    file_path: str


@app.post("/delete_file")
async def delete_file(req: DeleteRequest):
    raw = req.file_path.strip()

    if "/" in raw:
        _, target = raw.split("/", 1)
    else:
        target = raw

    print("Normalized delete target:", target)

    # STEP 1: Select all rows with matching prefix
    query = (
        supabase.table("documents")
        .select("id, file_path")
        .like("file_path", f"{target}%")
        .execute()
    )

    rows = query.data or []

    if not rows:
        return {"message": "No rows to delete", "deleted": []}

    ids = [r["id"] for r in rows]

    # STEP 2: Delete using IN clause
    delete_res = (
        supabase.table("documents")
        .delete()
        .in_("id", ids)
        .execute()
    )

    return {
        "message": f"Deleted {len(delete_res.data)} rows",
        "deleted": delete_res.data
    }


# ============================================================
# 4️⃣ RAG CHAT
# ============================================================
@app.post("/rag-chat")
async def rag_chat(query: str = Form(...)):

    # QUERY EMBEDDING (API instead of local model!)
    q_emb = embed_text_list([query])[0]

    # 1 — Search Supabase
    result = supabase.rpc(
        "match_documents",
        {
            "query_embedding": q_emb,
            "match_count": 20
        }
    ).execute()

    items = result.data or []

    # 2 — Priority scoring
    ranked = []
    for row in items:
        dist = row.get("distance", 1.0)
        pr = row.get("priority", 3)
        score = dist * (1 + (pr - 1) * 0.5)
        ranked.append((score, row))

    ranked.sort(key=lambda x: x[0])

    notes = [row for score, row in ranked if row["priority"] == 1][:3]
    docs  = [row for score, row in ranked if row["priority"] > 1][:4]

    top_chunks = [r["content"] for r in notes] + [r["content"] for r in docs]
    context = "\n\n".join(top_chunks)

    # literal shortcut
    if query.lower() in context.lower():
        return {"answer": context}

    # Gemini generation
    prompt = f"""
You are a Mount Sinai Radiology assistant.
Give ALL answers in plain text. No markdown. No asterisks.

Use the provided text below when answering.
Notes (priority 1) always override older or conflicting information from documents.
However, still include all other correct non-conflicting information from the documents.
If the document does not contain the answer, say I am unsure.

Context:
{context}

Question:
{query}
"""

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return {"answer": response.text.strip()}


# ============================================================
# 5️⃣ HEALTH
# ============================================================
@app.get("/")
def home():
    return {"message": "Supabase RAG Backend (HF Inference) running!"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}