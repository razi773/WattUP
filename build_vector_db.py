import os
from ingestion.extract_pdf import telecharger_et_extraire
from ingestion.split_chunks import diviser_en_chunks
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
def creer_vectorstore(texte_pdf=None):
    if texte_pdf is None:
        texte_pdf = telecharger_et_extraire()
    documents = diviser_en_chunks(texte_pdf)
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    vectordb = FAISS.from_documents(documents, embedding=embeddings)
    FAISS_INDEX_DIR = "embeddings/faiss_index"
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    vectordb.save_local(FAISS_INDEX_DIR)
    print(f"✅ Base vectorielle FAISS créée avec {model_name}")
    return vectordb
if __name__ == "__main__":
    creer_vectorstore()