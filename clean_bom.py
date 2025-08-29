#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour nettoyer tous les caractères BOM et autres caractères invisibles
"""

import os
import glob
import chardet

def clean_bom_characters(file_path):
    """Nettoie les caractères BOM d'un fichier"""
    try:
        # Lire le fichier en mode binaire pour détecter l'encodage
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        # Détecter l'encodage
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding', 'utf-8')
        
        # Décoder et nettoyer
        try:
            content = raw_data.decode(encoding)
        except:
            content = raw_data.decode('utf-8', errors='ignore')
        
        # Supprimer le BOM s'il existe
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # Supprimer autres caractères invisibles courants
        content = content.replace('\u200b', '')  # Zero Width Space
        content = content.replace('\u200c', '')  # Zero Width Non-Joiner
        content = content.replace('\u200d', '')  # Zero Width Joiner
        content = content.replace('\ufeff', '')  # BOM
        
        # Sauvegarder avec encodage UTF-8 sans BOM
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur avec {file_path}: {e}")
        return False

def clean_project_files():
    """Nettoie tous les fichiers Python du projet"""
    
    # Dossiers à traiter
    directories = ['ai_energy', 'face_auth', 'AI_Energy_Analyzer', 'templates', 'ingestion']
    file_extensions = ['*.py', '*.html', '*.js', '*.css']
    
    cleaned_count = 0
    
    for directory in directories:
        if os.path.exists(directory):
            for extension in file_extensions:
                pattern = os.path.join(directory, '**', extension)
                for file_path in glob.glob(pattern, recursive=True):
                    if clean_bom_characters(file_path):
                        print(f"✅ Nettoyé: {file_path}")
                        cleaned_count += 1
    
    # Nettoyer aussi les fichiers à la racine
    for extension in file_extensions:
        for file_path in glob.glob(extension):
            if clean_bom_characters(file_path):
                print(f"✅ Nettoyé: {file_path}")
                cleaned_count += 1
    
    print(f"\n🎉 Nettoyage terminé! {cleaned_count} fichiers traités.")

if __name__ == "__main__":
    print("🧹 Nettoyage des caractères BOM et invisibles...")
    clean_project_files()
