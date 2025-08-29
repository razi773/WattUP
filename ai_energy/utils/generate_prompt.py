# -*- coding: utf-8 -*-
"""
Module documentation
"""
def generer_prompt(resume_texte, texte_pdf_rag):
    return f"""
Tu es un expert en efficacité énergétique industrielle.
Analyse les données de consommation ci-dessous pour :
1. Évaluer la cohérence des prédictions mensuelles
2. Détecter les anomalies passées et probables
3. Fournir des recommandations claires et actionnables
---
📊 **Données de consommation (résumé + prédiction XGBoost)** :
{resume_texte}
📘 **Connaissances extraites du guide énergétique** :
{texte_pdf_rag}
---
Rédige une réponse structurée avec ce format :
Explique si la prédiction est réaliste ou non, en comparant aux valeurs moyennes et aux pics passés. Appuie-toi sur les concepts énergétiques du guide.
- Détaille les dates et causes potentielles
- Compare avec des cas similaires issus du guide si possible
Présente des actions concrètes et chiffrées dans ce format :
| Recommandation                  | Gain estimé   | Coût estimé  | Période de retour |
|--------------------------------|----------------|--------------|-------------------|
| Convertisseur de fréquence     | 1392 $/an      | 80 $         | 1.85 an           |
| Remplacement des lampes        | 1.50 $/an      | -            | -                 |
| Maintenance des ballasts       | 1.05 $/an      | -            | -                 |
Fais un résumé final avec des conseils clés à appliquer en priorité.
"""