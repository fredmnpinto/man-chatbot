# Linux Man-Page Chatbot (RAG-based)

This project implements a **retrieval-augmented language model (RAG) chatbot** for querying Linux manual pages using natural language.  
The system indexes locally available `man` pages and answers questions **only when relevant documentation is found**, preventing hallucinated responses.

The chatbot runs fully **offline**, using local embeddings, a FAISS vector index, and an open-source large language model served via Ollama.

---

## Features

- Natural language querying of Linux `man` pages
- Dense semantic retrieval using Sentence-BERT embeddings
- FAISS-based vector search over hundreds of thousands of documentation chunks
- Retrieval-confidence gating to suppress hallucinations
- Explicit references to relevant man pages in answers
- Fully local execution (no external APIs)

---

## Platform Support

- **Linux**: Fully supported (data extraction + inference)
- **macOS**: Inference only (requires prebuilt index from Linux)

Data extraction depends on the Linux man-page infrastructure (`man-db`, `mandb`, `apropos`) and is therefore **Linux-only**.

---

## System Requirements

### Operating System
- Linux (required for data extraction)

### Hardware (tested configuration)
- NVIDIA RTX 3060 Ti GPU
- 16 GB RAM  

The system also works on CPU-only setups, but response times will be slower.

### Software
- Python 3.9 or newer
- `man-db` (provides `man`, `mandb`, `apropos`)
- Ollama (for local LLM inference)

---

## Python Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
