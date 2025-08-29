# -*- coding: utf-8 -*-
"""
Module documentation
"""

from django import forms
class UploadCSVForm(forms.Form):
    csv_file = forms.FileField(label="Fichier CSV de consommation énergétique", required=True)
