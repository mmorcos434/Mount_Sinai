import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from sqlalchemy import create_engine
from PyPDF2 import PdfReader
import os


DB_PATH = "db/locations.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={'timeout': 30})


df = pd.read_sql("SELECT * FROM procedures", engine)


model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("procedures")


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

files = [
    "CT MRI Machine Weight Limit & Bore Size.md",
    "MAIN CAMPUS  MRI ROOM ASSIGNMENTS UPDATED 5.22.pdf",
    "# HESS & RA MRI Room Assignments.txt",
]

for file in files:
    path = os.path.join("data", "locations", file)
    if file.endswith(".md"):
        text = read_markdown(path)
    elif file.endswith(".pdf"):
        text = read_pdf(path)
    elif file.endswith(".txt"):
        text = read_text(path)
    else:
        continue
    
    if not text.strip():
        continue
    
    embedding = model.encode([text])[0]
    collection.add(
        embeddings=[embedding.tolist()],
        documents=[text],
        metadatas=[{"source": file}],
        ids=[file]
    )
    print(f"Files: {file}")

print(f"Total documents in collection: {collection.count()}")
