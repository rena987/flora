from openai import OpenAI
from dotenv import load_dotenv
import json
import faiss
import numpy as np
import os 
import pickle
import time

load_dotenv()
client = OpenAI()

index = None 
_index_built = False
documents = []
doc_names = []

INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index.pkl")

def build_index():
    global index, _index_built
    if _index_built:
        return

    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "rb") as f:
            data = pickle.load(f)
            index = data["index"]
            documents.extend(data["documents"])
            doc_names.extend(data["doc_names"])
        _index_built = True
        return

    kb_path = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
    for filename in os.listdir(kb_path):
        if not filename.endswith(".txt"):
            continue
        name = filename.replace(".txt", "")
        with open(os.path.join(kb_path, filename), "r", encoding="utf-8") as f:
            documents.append(f.read())
        doc_names.append(name)

    response = client.embeddings.create(input=documents, model="text-embedding-ada-002")
    embeddings = [item.embedding for item in response.data]
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))

    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"index": index, "documents": documents, "doc_names": doc_names}, f)

    _index_built = True

def retrieve(disease_name: str, plant_type: str) -> dict:
    query = f"treatment protocol and care information for {disease_name} affecting {plant_type} plant"

    response = client.embeddings.create(
        input=[query],
        model="text-embedding-ada-002"
    )

    query_vector = np.array([response.data[0].embedding], dtype=np.float32)

    distances, indices = index.search(query_vector, k=3)

    distances = np.empty((1, 3), dtype=np.float32)
    indices = np.empty((1, 3), dtype=np.int64)
    index.search(query_vector, 3, distances, indices)

    results = []
    for i in indices[0]:
        results.append({
            "document": doc_names[i],
            "content": documents[i]
        })
    
    return {
        "query": query,
        "results": results,
        "top_match": doc_names[indices[0][0]]
    }

if __name__ == "__main__":
    build_index()
    print(f"Index built with {len(documents)} documents")
    
    result = retrieve("Powdery Mildew", "Rose")
    print("\nTop match:", result["top_match"])
    print("\nTop document content:")
    print(result["results"][0]["content"])