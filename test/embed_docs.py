import os
import pandas as pd
from sqlalchemy import create_engine
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb

# === Config ===
DB_PATH = "db/locations.db"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "procedures"
DATA_DIR = "data/locations"

FILES = [
    "CT MRI Machine Weight Limit & Bore Size.md",
    "MAIN CAMPUS  MRI ROOM ASSIGNMENTS UPDATED 5.22.pdf",
    "# HESS & RA MRI Room Assignments.txt",
]

# === Setup ===
print("[INFO] Connecting to DB and Chroma...")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={'timeout': 30})
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# === Helpers ===
def read_markdown(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_pdf(path):
    text = ""
    reader = PdfReader(path)
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def already_exists(file_name):
    """Check if this file (by ID) is already stored in Chroma."""
    try:
        results = collection.get(ids=[file_name])
        return len(results["ids"]) > 0
    except Exception:
        return False

# === Embed and Add Files ===
for file in FILES:
    path = os.path.join(DATA_DIR, file)
    if not os.path.exists(path):
        print(f"[WARN] File not found: {file}")
        continue
    
    if already_exists(file):
        print(f"⏭️ Skipping (already exists): {file}")
        continue
    
    # Read file content
    if file.endswith(".md"):
        text = read_markdown(path)
    elif file.endswith(".pdf"):
        text = read_pdf(path)
    elif file.endswith(".txt"):
        text = read_text(path)
    else:
        print(f"[WARN] Unsupported file type: {file}")
        continue

    if not text.strip():
        print(f"[WARN] Empty file skipped: {file}")
        continue
    
    # Embed and add to collection
    embedding = model.encode([text])[0]
    collection.add(
        embeddings=[embedding.tolist()],
        documents=[text],
        metadatas=[{"source": "file", "filename": file}],
        ids=[file]
    )
    print(f"✅ Embedded and stored: {file}")

print(f"\n[INFO] Total documents now in collection: {collection.count()}")
engine.dispose()
