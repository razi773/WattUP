# -*- coding: utf-8 -*-
"""
RAG utils - FAISS version (chemin corrigé)
"""

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from pathlib import Path

# 📁 Chemin absolu vers le dossier contenant l’index FAISS
INDEX_DIR = Path(r"C:\Users\HP\Desktop\stage pfe\deploiement\deploiement-project\embeddings\faiss_index")

# 🧠 Charger les embeddings + index
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
faiss_index = FAISS.load_local(str(INDEX_DIR), embedding_model, allow_dangerous_deserialization=True)


def retrieve_context(query: str, top_k: int = 3) -> str:
    """
    Recherche les chunks les plus proches dans l’index FAISS pour enrichir le prompt
    """
    try:
        results = faiss_index.similarity_search(query, k=top_k)
        return "\n\n".join([doc.page_content for doc in results])
    except Exception as e:
        return f"⚠️ Erreur RAG FAISS : {str(e)}"
