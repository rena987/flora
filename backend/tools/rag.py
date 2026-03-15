from openai import OpenAI
from dotenv import load_dotenv
import json
import faiss
import numpy as np
import os 
import time

load_dotenv()
client = OpenAI()

index = None 
_index_built = False
documents = []
doc_names = []

def build_index():
    global index 
    global _index_built 

    if _index_built: 
        return 

    _index_built = True 

    kb_path = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
    for filename in os.listdir(kb_path):
        if not filename.endswith(".txt"):
            continue 
        name = filename.replace(".txt", "")
        complete_file = os.path.join(kb_path, filename)
        with open(complete_file, "r", encoding='utf-8') as file: 
            documents.append(file.read())
        doc_names.append(name)

    for attempt in range(3):
        try:
            response = client.embeddings.create(
                input=documents,
                model="text-embedding-ada-002"
            )
            break
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)

    embeddings = [item.embedding for item in response.data]
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    vectors = np.array(embeddings, dtype=np.float32)
    index.add(vectors)

def retrieve(disease_name: str, plant_type: str) -> dict:
    query = f"treatment protocol and care information for {disease_name} affecting {plant_type} plant"

    response = client.embeddings.create(
        input=[query],
        model="text-embedding-ada-002"
    )

    query_vector = np.array([response.data[0].embedding], dtype=np.float32)

    distances, indices = index.search(query_vector, k=3)

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