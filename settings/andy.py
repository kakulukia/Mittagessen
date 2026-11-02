import os

from .dev import *  # noqa

# DEBUG = False
DEBUG = True
WHATSAPP_OLLAMA_URL = os.environ.get("WHATSAPP_OLLAMA_URL", "http://192.168.188.57:11434")
