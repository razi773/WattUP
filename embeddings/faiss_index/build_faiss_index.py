from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Charger le texte
loader = TextLoader("anomalies.txt", encoding='utf-8')
documents = loader.load()

# Split en petits morceaux
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# Embedding
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Index FAISS
faiss_index = FAISS.from_documents(chunks, embedding_model)

# Sauvegarder
faiss_index.save_local("faiss_index")
print("✅ Index FAISS créé et sauvegardé.")
