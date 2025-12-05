import os
import json
import numpy as np
import google.generativeai as genai
import pdfplumber


from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv


from unstructured.partition.auto import partition
from uuid import uuid4
from sentence_transformers import SentenceTransformer


from supabase import create_client
from src.query_router import answer_scheduling_query


<<<<<<< Updated upstream
# ============================================================
# ENV + SUPABASE CLIENT
# ============================================================
=======
# ------------------------------
# ENV + Supabase Client
# ------------------------------
>>>>>>> Stashed changes
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

<<<<<<< Updated upstream

# ============================================================
# GEMINI CONFIG
# ============================================================
=======

# ------------------------------
# Sinai Nexus Scheduling Router
# ------------------------------
from src.query_router import answer_scheduling_query


# ------------------------------
# Gemini Setup
# ------------------------------
>>>>>>> Stashed changes
if os.getenv("GOOGLE_API_KEY"):
   genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
else:
   genai.configure()



<<<<<<< Updated upstream
# ============================================================
# LAZY-LOADED EMBEDDING MODEL
# ============================================================
embedding_model = None

def get_embedding_model():
    """Load SentenceTransformer only when first used."""
    global embedding_model
    if embedding_model is None:
        print("🔥 Loading embedding model (lazy load)...")
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return embedding_model


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
=======

# ------------------------------
# FastAPI App
# ------------------------------
app = FastAPI(title="Sinai Nexus Backend (Supabase RAG)")
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
>>>>>>> Stashed changes
)


class AgentChatRequest(BaseModel):
   question: str



# ============================================================
# 1️⃣ SCHEDULING AGENT
# ============================================================
@app.post("/agent-chat")
def agent_chat(payload: AgentChatRequest):
<<<<<<< Updated upstream
    try:
        answer = answer_scheduling_query(payload.question)
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}
=======
   """Deterministic scheduling Q&A"""
   try:
       answer = answer_scheduling_query(payload.question)
       return {"answer": answer}
   except Exception as e:
       return {"answer": f"Error: {str(e)}"}

>>>>>>> Stashed changes


# ============================================================
# 2️⃣ UPLOAD → PARSE → CHUNK → EMBED → SUPABASE
# ============================================================
@app.post("/upload")
<<<<<<< Updated upstream
async def upload_file(file: UploadFile, priority: int = Form(3)):
=======
async def upload_file(
   file: UploadFile = File(...),
   priority: int = Form(3),
   path: str = Form(...)        
):
   """
   Upload → Parse → Chunk → Embed → Insert into Supabase.
   """
  
   # TEMP SAVE DIRECTORY
   os.makedirs("uploads", exist_ok=True)
>>>>>>> Stashed changes


<<<<<<< Updated upstream
    # Save raw upload
    with open(path, "wb") as f:
        f.write(await file.read())

    # Parse JSON note
    if file.filename.lower().endswith(".json"):
        priority = 1  # notes always priority 1
        with open(path, "r") as f:
            data = json.load(f)
        text = data.get("content", "")
        chunks = [text] if text else []

    else:
        # Parse other docs
        elements = partition(filename=path)
        text = "\n".join([el.text for el in elements if el.text])

        chunk_size = 600
        overlap = 80
        chunks = [
            text[i:i + chunk_size]
            for i in range(0, len(text), chunk_size - overlap)
        ]

    # Lazy load embedding model
    model = get_embedding_model()
    embeddings = model.encode(chunks)

    # Insert chunks into Supabase
    rows = []
    for chunk, emb in zip(chunks, embeddings):
        rows.append({
            "content": chunk,
            "embedding": emb.tolist(),
            "priority": priority,
            "file_path": f"other-content/{file.filename}",
        })
=======
   # temp file used ONLY for parsing PDFs/DOCX
   local_path = f"uploads/{uuid4()}_{file.filename}"


   # Save file to temp local path
   with open(local_path, "wb") as f:
       f.write(await file.read())


   # Handle JSON Notes
   if file.content_type == "application/json":
       priority = 1
       with open(local_path, "r") as f:
           data = json.load(f)
       text = data.get("content", "")
       chunks = [text] if text else []


   else:
       # Parse PDFs / DOCX / MD / TXT
        if file.filename.lower().endswith(".pdf"):
            elements = []
            with pdfplumber.open(local_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        elements.append(text)
            text = "\n".join(elements)
        else:
            elements = partition(filename=local_path, strategy="text") #docx, pdfs, md
            text = "\n".join([el.text for el in elements if el.text])


        chunk_size = 600
        overlap = 80
        chunks = [
            text[i : i + chunk_size]
            for i in range(0, len(text), chunk_size - overlap)
        ]


   # Embed
   embeddings = embedding_model.encode(chunks)
>>>>>>> Stashed changes


<<<<<<< Updated upstream
    return {"message": f"Inserted {len(chunks)} chunks", "chunks_added": len(chunks)}


# ============================================================
# 3️⃣ DELETE FILE
# ============================================================
@app.post("/delete_file")
async def delete_file(file_path: str = Form(...)):
    supabase.table("documents").delete().eq("file_path", file_path).execute()
    return {"message": f"Deleted all chunks for {file_path}"}
=======
   # Store in Supabase
   rows = []
   for chunk, emb in zip(chunks, embeddings):
       rows.append({
           "content": chunk,
           "embedding": emb.tolist(),
           "priority": priority,
           "file_path": path       # <-- FULL PATH from frontend
       })


   if rows:
       supabase.table("documents").insert(rows).execute()


   return {
       "message": f"Inserted {len(chunks)} chunks into Supabase",
       "chunks_added": len(chunks),
       "stored_path": path
   }
# ===============================================================
# 3️⃣ Delete File Endpoint
# ===============================================================


class DeleteRequest(BaseModel):
   file_path: str


@app.post("/delete_file")
async def delete_file(req: DeleteRequest):
   response = (
       supabase.table("documents")
       .delete()
       .eq("file_path", req.file_path)
       .execute()
   )


   return {
       "message": f"Deleted {len(response.data)} chunks",
       "file_path_received": req.file_path,
       "deleted_rows": response.data,   
   }



>>>>>>> Stashed changes


# ============================================================
# 4️⃣ RAG CHAT
# ============================================================
@app.post("/rag-chat")
async def rag_chat(query: str = Form(...)):
<<<<<<< Updated upstream

    model = get_embedding_model()
    q_embed = model.encode([query]).tolist()[0]

    # Supabase vector search
    result = supabase.rpc(
        "match_documents",
        {"query_embedding": q_embed, "match_count": 20}
    ).execute()
=======
   q_embed = embedding_model.encode([query]).tolist()[0]

>>>>>>> Stashed changes

   # 1. Search Supabase
   result = supabase.rpc(
       "match_documents",
       {
           "query_embedding": q_embed,
           "match_count": 20   # get enough results to rank properly
       }
   ).execute()

<<<<<<< Updated upstream
    # Priority re-ranking
    scored = []
    for row in items:
        dist = row.get("distance", 1.0)
        pr = row.get("priority", 3)
        score = dist * (1.0 + (pr - 1) * 0.5)
        scored.append((score, row))
=======

   items = result.data or []

>>>>>>> Stashed changes

   # 2. Priority scoring (notes = priority 1 → strongest weight)
   scored = []
   for row in items:
       dist = row.get("distance", 1.0)
       pr = row.get("priority", 3)

<<<<<<< Updated upstream
    notes = [row for _, row in scored if row["priority"] == 1][:3]
    docs =  [row for _, row in scored if row["priority"] > 1][:4]

    top_chunks = [row["content"] for row in notes] + \
                 [row["content"] for row in docs]
=======

       # Lower distance is better — priority 1 gets strongest influence
       score = dist * (1.0 + (pr - 1) * 0.5)
>>>>>>> Stashed changes


<<<<<<< Updated upstream
    # STOP-SEARCH optimization
    if query.lower() in context.lower():
        return {"answer": context}

    prompt = f"""
You are a Mount Sinai Radiology assistant.
Provide answers in plain text only.
=======
       scored.append((score, row))


   scored.sort(key=lambda x: x[0])


   # 3. Separate notes (priority 1) and docs (priority > 1)
   notes = [row for score, row in scored if row["priority"] == 1][:3]   # top 3 notes
   docs  = [row for score, row in scored if row["priority"] > 1][:4]   # top 4 doc chunks


   # 4. Combine context
   top_chunks = [row["content"] for row in notes] + \
                [row["content"] for row in docs]


   context = "\n\n".join(top_chunks)


   # 5. STOP-SEARCH: if query text literally appears in context
   if query.lower() in context.lower():
       return {"answer": context}


   # 6. Gemini Prompt
   prompt = f"""
You are a Mount Sinai Radiology assistant.
Give ALL answers in plain text. No markdown. No asterisks.


Use the provided text below when answering.
Notes (priority 1) always override older or conflicting information from documents.
However, still include all other correct non-conflicting information from the documents.
If the document does not contain the answer, say I am unsure.
>>>>>>> Stashed changes


Context:
{context}


Question:
{query}
"""


   model = genai.GenerativeModel("gemini-2.5-flash")
   response = model.generate_content(prompt)


   return {"answer": response.text.strip()}




# ============================================================
# HEALTH CHECKS
# ============================================================
@app.get("/")
def home():
<<<<<<< Updated upstream
    return {"message": "Supabase RAG Backend is running!"}


@app.get("/healthz")
def health():
    return {"status": "ok"}


# ============================================================
# RENDER ENTRYPOINT
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
=======
   return {"message": "Supabase RAG Backend is running!"}
>>>>>>> Stashed changes
