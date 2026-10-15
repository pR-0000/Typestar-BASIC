"""Studio UI translation. BASIC source and asset identifiers remain unchanged."""
import json
import os
from pathlib import Path
_language = os.environ.get('TYPESTAR_STUDIO_LANGUAGE', 'en')
_catalog = json.loads(Path(__file__).with_name('translations.json').read_text(encoding='utf-8'))

def set_language(language):
    global _language
    _language = language if language in ('en', 'fr') else 'en'

def language():
    return _language

def tr(text):
    return _catalog.get(text, text) if _language == 'en' else text
