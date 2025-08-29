# -*- coding: utf-8 -*-
"""
Module documentation
"""
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
model_id = "meta-llama/Llama-3.2-1B-Instruct"
client = InferenceClient(model=model_id, token=HF_TOKEN)
def envoyer_a_zephyr(prompt):
    try:
        system_message = (
            "Tu es un expert en analyse énergétique. "
            "Donne toujours des réponses détaillées, structurées et pédagogiques. "
            "Toutes les valeurs monétaires doivent être exprimées en dinars tunisiens (DT). "
            "Si les montants sont initialement en dollars ($), convertis-les en dinars tunisiens au taux de 1 $ = 3,1 DT, "
            "et indique clairement que la conversion a été effectuée."
        )
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=700,
            top_p=0.9,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"Erreur LLaMA : {str(e)}"