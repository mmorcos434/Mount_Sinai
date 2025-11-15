import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from sqlalchemy import create_engine, inspect
import shutil
import os

DB_PATH = "db/locations.db"

# Load database
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={'timeout': 30})

inspector = inspect(engine)
print("Tables in DB:", inspector.get_table_names())

df = pd.read_sql("SELECT * FROM procedures", engine)

# Initialize embedding model
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
print(f"Model dimension: {model.get_sentence_embedding_dimension()}")

# Create fresh client
client = chromadb.PersistentClient(path="./chroma_db")

if "procedures" in [c.name for c in client.list_collections()]:
    collection = client.get_collection("procedures")
    print("🔄 Using existing Chroma collection.")
else:
    collection = client.create_collection("procedures")
    print("🆕 Created new Chroma collection.")

print(f"Collection contacts {collection.count()} documents")

# Create embeddings
embeddings = model.encode(df["summary"].tolist())
print(f"Embeddings shape: {embeddings.shape}")

# Store in Chroma
documents = df["summary"].tolist()
metadatas = [{"source": "excel", "procedure": row["EAP Name"]} for _, row in df.iterrows()]
ids = [str(i) for i in range(len(df))]

collection.add(
    embeddings=embeddings.tolist(),  # Explicitly pass embeddings
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print(f"✅ Added {len(df)} records to Chroma collection 'procedures'.")

engine.dispose()






