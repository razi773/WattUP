# -*- coding: utf-8 -*-
"""
Module documentation
"""
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
FAISS_INDEX_DIR = "embeddings/faiss_index"
def interroger_rag(question: str, k: int = 5) -> str:
    """
    Recherche dans la base FAISS (vectorisée avec HuggingFaceEmbeddings)
    les k passages les plus pertinents pour la question donnée.
    Retourne un bloc de texte concaténé, prêt à intégrer dans un prompt.
    """
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = FAISS.load_local(
    FAISS_INDEX_DIR,
    embeddings,
    allow_dangerous_deserialization=True  
        )
    retriever = vectordb.as_retriever(search_type="similarity", k=k)
    documents = retriever.get_relevant_documents(question)
    contexte = "\n\n".join([doc.page_content for doc in documents])
    return contexte
if __name__ == "__main__":
    question = "Quels sont les types d’anomalies énergétiques fréquentes selon le guide ?"
    contexte = interroger_rag(question)
    print("\n--- Contexte RAG extrait ---\n")
    print(contexte)
