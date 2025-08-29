import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from ingestion.extract_pdf import telecharger_et_extraire
from ingestion.split_chunks import diviser_en_chunks
load_dotenv()
FAISS_INDEX_DIR = "embeddings/faiss_index"
def creer_vectorstore(texte_pdf=None):
    if texte_pdf is None:
        texte_pdf = telecharger_et_extraire()
    documents = diviser_en_chunks(texte_pdf)
    embeddings = OpenAIEmbeddings()
    vectordb = FAISS.from_documents(documents, embedding=embeddings)
    os.makedirs(os.path.dirname(FAISS_INDEX_DIR), exist_ok=True)
    vectordb.save_local(FAISS_INDEX_DIR)
    print(f"✅ Base vectorielle FAISS créée dans {FAISS_INDEX_DIR}")
    return vectordb
if __name__ == "__main__":
    creer_vectorstore()