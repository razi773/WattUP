# -*- coding: utf-8 -*-
"""
Module documentation
"""

import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_Energy_Analyzer.settings')
application = get_wsgi_application()
