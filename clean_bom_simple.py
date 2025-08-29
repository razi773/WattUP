#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple pour nettoyer les caractères BOM
"""

import os
import glob

def clean_bom_simple(file_path):
    """Nettoie les caractères BOM d'un fichier - version simple"""
    try:
        # Lire en mode binaire d'abord
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        # Décoder en UTF-8
        try:
            content = raw_data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = raw_data.decode('utf-8-sig')  # UTF-8 avec BOM
            except:
                content = raw_data.decode('latin-1', errors='ignore')
        
        # Supprimer le BOM s'il existe
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # Supprimer autres caractères invisibles
        content = content.replace('\u200b', '')  # Zero Width Space
        content = content.replace('\u200c', '')  # Zero Width Non-Joiner
        content = content.replace('\u200d', '')  # Zero Width Joiner
        content = content.replace('\ufeff', '')  # BOM supplémentaires
        
        # Sauvegarder avec encodage UTF-8 sans BOM
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur avec {file_path}: {e}")
        return False

def clean_all_python_files():
    """Nettoie tous les fichiers Python du projet"""
    
    python_files = []
    
    # Dossiers à traiter
    directories = ['ai_energy', 'face_auth', 'AI_Energy_Analyzer', 'ingestion']
    
    # Ajouter les fichiers Python à la racine
    for file in glob.glob('*.py'):
        python_files.append(file)
    
    # Ajouter les fichiers Python des dossiers
    for directory in directories:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(os.path.join(root, file))
    
    cleaned_count = 0
    
    for file_path in python_files:
        if clean_bom_simple(file_path):
            print(f"✅ Nettoyé: {file_path}")
            cleaned_count += 1
    
    print(f"\n🎉 Nettoyage terminé! {cleaned_count} fichiers Python traités.")

if __name__ == "__main__":
    print("🧹 Nettoyage des caractères BOM dans les fichiers Python...")
    clean_all_python_files()
