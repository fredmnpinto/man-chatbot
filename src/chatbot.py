import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import ollama
import subprocess

# === Paths ===
DATA_PATH = Path(__file__).parent.parent / 'data'  # parent of src
PAGES_PATH = DATA_PATH / 'pages'
OLLAMA_CMD = "/usr/local/bin/ollama"

FAISS_INDEX_PATH = DATA_PATH / "faiss.index"
CHUNKS_PATH = DATA_PATH / "chunks.json"
META_PATH = DATA_PATH / "meta.json"
# === Parameters ===
TOP_K = 3

# === Helper Functions ===
def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def man_page_to_text(page: dict) -> str:
    """Flatten man page JSON into text."""
    text = []
    for section, content in page.items():
        if isinstance(content, dict):
            for key, value in content.items():
                if key == 'CONTEXT':
                    text.append("\n".join(value))
                else:
                    text.append(f"{key}: {value}")
        else:
            text.append(content)
    return "\n".join(text)


def build_faiss_index():
    model = SentenceTransformer("all-MiniLM-L6-v2")

    chunk_texts = []
    chunk_sources = []

    for f in PAGES_PATH.glob("*.json"):
        page = json.load(open(f))
        full_text = man_page_to_text(page)

        if not full_text.strip():
            continue

        chunks = chunk_text(full_text)

        for i, chunk in enumerate(chunks):
            chunk_texts.append(chunk)
            chunk_sources.append(f"{f.stem}::chunk{i}")

    if not chunk_texts:
        raise ValueError("No chunks created from man pages")

    embeddings = model.encode(
        chunk_texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    return index, chunk_sources, chunk_texts, model


def save_index(index, chunk_texts, chunk_sources):
    faiss.write_index(index, str(FAISS_INDEX_PATH))

    with open(CHUNKS_PATH, "w") as f:
        json.dump(chunk_texts, f)

    with open(META_PATH, "w") as f:
        json.dump(chunk_sources, f)


def load_or_build_index():
    if (
        FAISS_INDEX_PATH.exists()
        and CHUNKS_PATH.exists()
        and META_PATH.exists()
    ):
        print("Loading existing FAISS index...")
        index = faiss.read_index(str(FAISS_INDEX_PATH))

        with open(CHUNKS_PATH) as f:
            chunk_texts = json.load(f)

        with open(META_PATH) as f:
            chunk_sources = json.load(f)

        model = SentenceTransformer("all-MiniLM-L6-v2")
        return index, chunk_sources, chunk_texts, model

    print("Building FAISS index...")
    index, chunk_sources, chunk_texts, model = build_faiss_index()
    save_index(index, chunk_texts, chunk_sources)
    return index, chunk_sources, chunk_texts, model


def ollama_query(prompt: str, model="llama2") -> str:
    cmd = [OLLAMA_CMD, "run", model]

    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Ollama CLI error:\n{result.stderr}")

    return result.stdout.strip()


def query_chatbot(user_query, index, docs, texts, model, top_k=3):
    query_emb = model.encode(
        [user_query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    D, I = index.search(query_emb, top_k)

    context = "\n\n".join(texts[i] for i in I[0])

    prompt = f"""
You are a Linux man page assistant.
Answer using ONLY the context below.

Context:
{context}

Question:
{user_query}
"""

    return ollama_query(prompt, model="mistral")


# === Main ===
if __name__ == "__main__":
    print("Building FAISS index...")
    index, docs, texts, model = load_or_build_index()
    print(f"FAISS index built with {len(docs)} documents.")

    print("\nLinux Man Page Chatbot (type 'exit' to quit)")
    while True:
        user_query = input("\nYou: ")
        if user_query.lower() in ['exit', 'quit']:
            break
        answer = query_chatbot(user_query, index, docs, texts, model)
        print(f"\nBot: {answer}")