import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os

from config import CHROMA_DB_PATH

# Initialize embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Collections
style_guides_collection = chroma_client.get_or_create_collection(
    name="style_guides",
    metadata={"hnsw:space": "cosine"}
)

remotion_docs_collection = chroma_client.get_or_create_collection(
    name="remotion_docs",
    metadata={"hnsw:space": "cosine"}
)


def seed_style_guides():
    """Seed style guides collection on first run."""
    if style_guides_collection.count() > 0:
        return
    
    guides = [
        {
            "id": "wedding",
            "text": "Wedding videos should be elegant and romantic. Use soft transitions, warm captions, and moderate pacing. Focus on emotional moments and beautiful details.",
            "metadata": {"type": "wedding", "tone": "romantic"}
        },
        {
            "id": "birthday",
            "text": "Birthday videos should be fun and celebratory. Use upbeat transitions, cheerful captions, and fast pacing. Include party moments and happy expressions.",
            "metadata": {"type": "birthday", "tone": "cheerful"}
        },
        {
            "id": "corporate",
            "text": "Corporate videos should be professional and clean. Use smooth transitions, formal captions, and moderate pacing. Focus on business moments and professional settings.",
            "metadata": {"type": "corporate", "tone": "professional"}
        },
        {
            "id": "travel",
            "text": "Travel videos should be adventurous and scenic. Use dynamic transitions, descriptive captions, and varied pacing. Show landscapes and exploration moments.",
            "metadata": {"type": "travel", "tone": "adventurous"}
        }
    ]
    
    for guide in guides:
        embedding = embedding_model.encode(guide["text"]).tolist()
        style_guides_collection.add(
            documents=[guide["text"]],
            embeddings=[embedding],
            ids=[guide["id"]],
            metadatas=[guide["metadata"]]
        )


def seed_remotion_docs():
    """Seed Remotion documentation collection on first run."""
    if remotion_docs_collection.count() > 0:
        return
    
    docs = [
        {
            "id": "sequence",
            "text": "Sequence component in Remotion is used to arrange clips in a timeline. Use it to display multiple images in order with transitions.",
            "metadata": {"component": "Sequence", "usage": "timeline"}
        },
        {
            "id": "img",
            "text": "Img component displays images in Remotion. Use it with absolute positioning and fill the frame. Supports src prop for image URL.",
            "metadata": {"component": "Img", "usage": "display"}
        },
        {
            "id": "absolutefill",
            "text": "AbsoluteFill is a layout component that fills the entire composition. Use it to make images cover the full frame.",
            "metadata": {"component": "AbsoluteFill", "usage": "layout"}
        },
        {
            "id": "interpolate",
            "text": "interpolate function creates smooth animations between values. Use it for fade in/out effects and transitions.",
            "metadata": {"component": "interpolate", "usage": "animation"}
        },
        {
            "id": "fade",
            "text": "Fade transition gradually changes opacity. Use fadeIn and fadeOut for smooth image transitions in slideshows.",
            "metadata": {"component": "fade", "usage": "transition"}
        },
        {
            "id": "crossfade",
            "text": "Crossfade transition blends two images together. Use it for elegant slideshow transitions between scenes.",
            "metadata": {"component": "crossfade", "usage": "transition"}
        }
    ]
    
    for doc in docs:
        embedding = embedding_model.encode(doc["text"]).tolist()
        remotion_docs_collection.add(
            documents=[doc["text"]],
            embeddings=[embedding],
            ids=[doc["id"]],
            metadatas=[doc["metadata"]]
        )


def get_style_guide(query: str, n_results: int = 2) -> List[Dict]:
    """Retrieve relevant style guides from ChromaDB."""
    query_embedding = embedding_model.encode(query).tolist()
    results = style_guides_collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    guides = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            guides.append({
                "text": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
            })
    return guides


def get_remotion_docs(query: str, n_results: int = 3) -> List[Dict]:
    """Retrieve relevant Remotion documentation from ChromaDB."""
    query_embedding = embedding_model.encode(query).tolist()
    results = remotion_docs_collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    docs = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            docs.append({
                "text": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
            })
    return docs


def initialize_rag():
    """Initialize RAG by seeding collections if needed."""
    seed_style_guides()
    seed_remotion_docs()