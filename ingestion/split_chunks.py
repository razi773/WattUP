from langchain.text_splitter import RecursiveCharacterTextSplitter
def diviser_en_chunks(texte_brut, chunk_size=800, chunk_overlap=100):
    """
    Divise le texte PDF en paragraphes pour le RAG
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    documents = splitter.create_documents([texte_brut])
    print(f"✔️ {len(documents)} chunks générés à partir du texte PDF.")
    return documents
if __name__ == "__main__":
    from extract_pdf import telecharger_et_extraire
    texte = telecharger_et_extraire()
    chunks = diviser_en_chunks(texte)
    print(chunks[0].page_content)