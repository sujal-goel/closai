"""
LangChain RAG Service — System Design Knowledge Base
=====================================================
Indexes dataset.jsonl using Google Generative AI Embeddings + FAISS vector store.
Runs indexing in a background thread to not block server startup.
Provides a search_theory() function used by the blueprint generation pipeline.
"""
import json
import logging
import os
import threading
from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)

# Singleton vector store — populated in background after startup
_vectorstore: Optional[FAISS] = None
_is_ready = False


def _parse_dataset_to_documents(max_docs: int = 3000) -> list[Document]:
    """
    Parse the JSONL dataset into LangChain Documents.
    Each Document represents a heading section + its body text.
    max_docs caps the number of article sections to keep embedding time practical.
    """
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "dataset.jsonl")
    if not os.path.exists(dataset_path):
        logger.warning(f"Knowledge dataset not found at {dataset_path}")
        return []

    docs = []
    with open(dataset_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            if len(docs) >= max_docs:
                break
            try:
                doc = json.loads(line.strip())
                blocks = None
                if isinstance(doc, list):
                    blocks = doc
                elif isinstance(doc, dict):
                    for key in ("text", "content", "blocks", "sections", "data"):
                        candidate = doc.get(key)
                        if isinstance(candidate, list) and candidate and isinstance(candidate[0], dict) and "type" in candidate[0]:
                            blocks = candidate
                            break

                if not blocks:
                    continue

                current_heading = doc.get("title", "System Design") if isinstance(doc, dict) else "System Design"
                current_texts: list[str] = []

                for block in blocks:
                    btype = block.get("type", "")
                    bval = block.get("value", "").strip()
                    if not bval:
                        continue
                    if btype == "heading":
                        if current_texts:
                            docs.append(Document(
                                page_content=f"{current_heading}\n\n" + "\n".join(current_texts),
                                metadata={"heading": current_heading}
                            ))
                        current_heading = bval
                        current_texts = []
                    elif btype in ("text", "paragraph"):
                        current_texts.append(bval)

                if current_texts:
                    docs.append(Document(
                        page_content=f"{current_heading}\n\n" + "\n".join(current_texts),
                        metadata={"heading": current_heading}
                    ))

            except Exception:
                continue

    logger.info(f"Parsed {len(docs)} sections from dataset.jsonl")
    return docs


def _build_vectorstore():
    """Runs in a background thread to build the FAISS index without blocking startup."""
    global _vectorstore, _is_ready

    from config import get_settings
    settings = get_settings()

    if not settings.has_gemini:
        logger.warning("GEMINI_API_KEY not set — RAG knowledge base disabled.")
        return

    logger.info("🧠 Building LangChain RAG Knowledge Base (background)...")

    try:
        docs = _parse_dataset_to_documents(max_docs=3000)
        if not docs:
            logger.warning("No documents parsed — Knowledge Base empty.")
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=80,
            separators=["\n\n", "\n", ". ", " "],
        )
        chunks = splitter.split_documents(docs)
        logger.info(f"Chunked into {len(chunks)} pieces, starting embedding...")

        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-2-preview",
            google_api_key=settings.gemini_api_key,
        )

        _vectorstore = FAISS.from_documents(chunks, embeddings)
        _is_ready = True
        logger.info("✅ FAISS vector index ready — RAG Knowledge Base online!")

    except Exception as e:
        logger.error(f"❌ Failed to build RAG Knowledge Base: {e}")


def init_knowledge_base():
    """
    Called on app startup. Spins up a background thread to build the FAISS index
    so the server starts instantly and RAG becomes available shortly after.
    """
    thread = threading.Thread(target=_build_vectorstore, daemon=True, name="rag-indexer")
    thread.start()
    logger.info("📚 RAG indexer started in background — server is already live!")


async def search_theory(query: str, top_k: int = 3) -> str:
    """
    Semantic similarity search over the theory vector store.
    Returns a formatted string of the top_k most relevant theory excerpts.
    If the index isn't warmed up yet, returns an empty string gracefully.
    """
    if not _is_ready or _vectorstore is None:
        logger.debug("Knowledge Base still warming up — skipping RAG for this request.")
        return ""

    try:
        results = _vectorstore.similarity_search(query, k=top_k)
        if not results:
            return ""

        context = "### SYSTEM DESIGN THEORY CONTEXT ###\n"
        for i, doc in enumerate(results, 1):
            heading = doc.metadata.get("heading", "Theory")
            context += f"\n--- Theory {i}: {heading} ---\n{doc.page_content}\n"
        return context

    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return ""
