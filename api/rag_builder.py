"""
rag_builder.py — Builds per-lab FAISS vector stores from experiment documents.

Called at FastAPI startup so every lab's knowledge base is ready before the first chat.
Uses MMR (Maximal Marginal Relevance) retrieval to return diverse, non-repetitive context.
"""

import os
import json
import logging
from typing import Dict, Tuple

logger = logging.getLogger("poc_ai_lab.rag")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root
DATA_DIR = os.path.join(BASE_DIR, "data")
LAB_DOCS_DIR = os.path.join(DATA_DIR, "LAB", "Word")

# ---------------------------------------------------------------------------
# Cache  — one vectorstore per lab_id
# ---------------------------------------------------------------------------
_stores: Dict[str, object] = {}   # {lab_id: FAISS vectorstore}
_retrievers: Dict[str, object] = {} # {lab_id: retriever}


def _get_embeddings(api_key: str):
    """Return an NVIDIAEmbeddings instance (lazy import)."""
    from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
    from api.rate_limiter import embed_limiter
    
    # Apply rate limiting before creating/using embeddings in a batch
    embed_limiter.wait()
    
    return NVIDIAEmbeddings(
        model="nvidia/nv-embedqa-e5-v5",
        nvidia_api_key=api_key,
    )


def _load_documents() -> list:
    """Load Procedure.md (if exists) and all DOCX files in LAB/Word."""
    docs = []
    
    # 1. Procedure.md
    proc_path = os.path.join(LAB_DOCS_DIR, "Procedure.md")
    if os.path.exists(proc_path):
        try:
            # Simple file read to avoid unstructured dependency issues
            with open(proc_path, "r", encoding="utf-8") as f:
                content = f.read()
            from langchain_core.documents import Document
            # Split at experiment headers to create natural chunks
            sections = content.split("\n## ")
            for sec in sections:
                if len(sec.strip()) > 100:
                    docs.append(Document(
                        page_content=sec.strip(),
                        metadata={"source": "Procedure.md", "type": "procedure"}
                    ))
            logger.info("✅ Loaded Procedure.md — %d sections", len(sections))
        except Exception as e:
            logger.error("❌ Failed to load Procedure.md: %s", e)

    # 2. DOCX files
    if os.path.exists(LAB_DOCS_DIR):
        for fname in os.listdir(LAB_DOCS_DIR):
            if fname.lower().endswith(".docx"):
                fpath = os.path.join(LAB_DOCS_DIR, fname)
                try:
                    import docx2txt
                    text = docx2txt.process(fpath)
                    if text and len(text.strip()) > 50:
                        from langchain_core.documents import Document
                        docs.append(Document(
                            page_content=text.strip(),
                            metadata={"source": fname, "type": "docx"}
                        ))
                        logger.info("  ✅ Loaded DOCX: %s (%d chars)", fname, len(text))
                except Exception as e:
                    logger.warning("  ⚠️ Could not load %s: %s", fname, e)

    # 3. Experiment JSON data as additional context docs
    exps_path = os.path.join(DATA_DIR, "exps.json")
    if os.path.exists(exps_path):
        try:
            with open(exps_path, "r", encoding="utf-8") as f:
                exps = json.load(f)
            from langchain_core.documents import Document
            for exp_id, exp in exps.items():
                # Build a rich text block from each experiment
                lines = [f"EXPERIMENT: {exp_id}"]
                lines.append(f"Apparatus: {exp.get('apparatus', '')}")
                lines.append(f"Description: {exp.get('short_desc', '')}")
                lines.append(f"Narration: {exp.get('narration_script', '')}"[:1000])
                
                for obj in exp.get("objectives", []):
                    lines.append(f"Objective: {obj}")
                for kp in exp.get("key_points", []):
                    lines.append(f"Key Point: {kp}")
                for f_str in exp.get("formulas", []):
                    lines.append(f"Formula: {f_str}")
                    
                theory = exp.get("theory", {})
                for k, v in theory.items():
                    lines.append(f"Theory — {k}: {v}")

                docs.append(Document(
                    page_content="\n".join(lines),
                    metadata={"source": "exps.json", "exp_id": exp_id, "type": "experiment"}
                ))
            logger.info("✅ Loaded %d experiments from exps.json into RAG", len(exps))
        except Exception as e:
            logger.error("❌ Failed to load exps.json: %s", e)

    return docs


def _split_documents(docs: list) -> list:
    """Split long documents into manageable chunks."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(docs)
    logger.info("📄 Split %d docs → %d chunks", len(docs), len(chunks))
    return chunks


def build_lab_store(lab_id: str, api_key: str) -> Tuple[object, object]:
    """
    Build (or return cached) FAISS vectorstore + MMR retriever for a lab.
    
    Returns (vectorstore, retriever) tuple.
    """
    if lab_id in _stores:
        logger.debug("♻️ Returning cached vector store for lab: %s", lab_id)
        return _stores[lab_id], _retrievers[lab_id]

    logger.info("🔨 Building RAG vector store for lab: %s", lab_id)
    
    try:
        from langchain_community.vectorstores import FAISS
        
        docs = _load_documents()
        if not docs:
            logger.warning("⚠️ No documents found for lab %s — RAG will be empty", lab_id)
            return None, None
        
        chunks = _split_documents(docs)
        embeddings = _get_embeddings(api_key)
        
        logger.info("🔢 Creating FAISS index from %d chunks…", len(chunks))
        vectorstore = FAISS.from_documents(chunks, embeddings)
        
        # MMR retriever: fetch_k=20 candidates, return k=5 most diverse
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20}
        )
        
        _stores[lab_id] = vectorstore
        _retrievers[lab_id] = retriever
        
        logger.info("✅ RAG vector store ready for lab %s — %d chunks indexed", lab_id, len(chunks))
        return vectorstore, retriever
        
    except Exception as e:
        logger.error("❌ Failed to build vector store for lab %s: %s", lab_id, e)
        return None, None


def get_retriever(lab_id: str) -> object:
    """Get the retriever for a lab (must have been built first)."""
    return _retrievers.get(lab_id)


def invalidate(lab_id: str):
    """Clear cached store for a lab (call after adding/removing experiments)."""
    _stores.pop(lab_id, None)
    _retrievers.pop(lab_id, None)
    logger.info("🗑️ Cleared RAG cache for lab: %s", lab_id)


def build_all(labs: dict, get_key_fn):
    """Build stores for all labs at startup. labs = {lab_id: lab_config}."""
    logger.info("🚀 Building RAG stores for %d lab(s)…", len(labs))
    for lab_id, lab_config in labs.items():
        try:
            key = get_key_fn(lab_id)
            if not key:
                logger.warning("⚠️ No API key available for lab %s — skipping RAG build", lab_id)
                continue
            build_lab_store(lab_id, key)
        except Exception as e:
            logger.error("❌ Error building store for lab %s: %s", lab_id, e)
