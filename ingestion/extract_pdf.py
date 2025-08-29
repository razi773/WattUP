import fitz  
import requests
import os
PDF_URL = "https://ressources-naturelles.canada.ca/sites/nrcan/files/oee/files/pdf/publications/pub/peeic/guide-et-outil-de-verification-energetique.pdf"
LOCAL_PATH = "data/guide_verification_energetique.pdf"
def telecharger_pdf(url=PDF_URL, save_path=LOCAL_PATH):
    if not os.path.exists(save_path):
        print(f"Téléchargement du PDF depuis {url}...")
        response = requests.get(url)
        with open(save_path, "wb") as f:
            f.write(response.content)
        print("Téléchargement terminé.")
    else:
        print("PDF déjà téléchargé.")
def extraire_texte_pdf(pdf_path=LOCAL_PATH):
    print(f"Extraction du texte depuis {pdf_path}...")
    doc = fitz.open(pdf_path)
    texte = "\n".join([page.get_text() for page in doc])
    doc.close()
    return texte.strip()
def telecharger_et_extraire():
    telecharger_pdf()
    texte = extraire_texte_pdf()
    return texte
if __name__ == "__main__":
    texte_pdf = telecharger_et_extraire()
    print(texte_pdf[:1000])  