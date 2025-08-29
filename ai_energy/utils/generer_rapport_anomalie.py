# -*- coding: utf-8 -*-
import os
import threading
import pandas as pd
from huggingface_hub import InferenceClient
from ai_energy.utils.rag_utils import retrieve_context

# 🔐 Récupération du token d’authentification
hf_token = os.getenv("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")  # Vérifie qu’il est bien exporté

# ✅ Client avec modèle validé
client = InferenceClient(
    model="meta-llama/Meta-Llama-Guard-2-8B",
    token=hf_token
)

class TimeoutException(Exception):
    pass

def run_with_timeout(func, args=(), kwargs={}, timeout=180):
    result = {}
    def wrapper():
        try:
            result['value'] = func(*args, **kwargs)
        except Exception as e:
            result['error'] = e
    thread = threading.Thread(target=wrapper)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutException("⏰ Temps d'exécution dépassé.")
    if 'error' in result:
        raise result['error']
    return result.get('value')

def generer_rapport_anomalie(anomalies_df: pd.DataFrame):
    if anomalies_df.empty:
        return "✅ Aucune anomalie détectée dans les données énergétiques."

    prompt = (
        "Tu es un expert en efficacité énergétique industrielle.\n"
        "Voici une série d'anomalies détectées dans une entreprise :\n"
    )

    for i, (_, row) in enumerate(anomalies_df.iterrows()):
        if i >= 10:
            break
        prompt += f"- 📅 {row['date']} : erreur détectée = {round(row['reconstruction_error'], 4)}\n"

    prompt += (
        "\nPour chaque date, donne :\n"
        "🟡 Une hypothèse sur la cause (ex : capteur défaillant, consommation anormale...)\n"
        "🛠️ Une recommandation concrète pour résoudre ou prévenir l'anomalie.\n"
        "Structure la réponse par date. Utilise des paragraphes clairs, des emojis professionnels et un ton sérieux.\n"
    )

    # 📚 Ajouter contexte RAG
    context = retrieve_context(prompt, top_k=3)
    final_prompt = f"📘 Contexte documentaire :\n{context}\n\n📩 Question :\n{prompt}"

    print("🧠 Prompt final envoyé au LLM :\n", final_prompt[:500], "...\n")

    try:
        def generate():
            response = client.chat.completions.create(
                model="meta-llama/Meta-Llama-Guard-2-8B",
                messages=[
                    {"role": "user", "content": final_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()

        return run_with_timeout(generate, timeout=180)

    except TimeoutException as e:
        return str(e)
    except Exception as e:
        return f"❌ Erreur lors de la génération : {str(e)}"
