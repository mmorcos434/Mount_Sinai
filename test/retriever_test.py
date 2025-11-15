from sentence_transformers import SentenceTransformer #fix do inference provider faster and dont save to computer storage
import chromadb

def retrieve(query, collection, model, n = 1):

    query_emb = model.encode([query])
    results = collection.query(query_embeddings=query_emb, n_results=n)

    if not results["documents"]:
        print("No relevant results found.")
        return []

    combined = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        score = 1 - dist
        combined.append({"text": doc, "meta": meta, "score": score})

    # Optional: re-rank so notes come first
    combined.sort(key=lambda x: x["score"] + (0.2 if x["meta"].get("source") == "notes" else 0), reverse=True)

    return combined


model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("procedures")

print("Collections:", [c.name for c in client.list_collections()]) 
print("Documents in 'procedures':", collection.count())

query = "Which locations do ct abscess drainage?"
results = retrieve(query, collection, model)

if not results:
    print("No matches found.")

for r in results:
    print(f"Score: {r['score']:.3f} | Source: {r['meta']['source']}")
    print(f"→ {r['text']}\n")

