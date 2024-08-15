import os

from dotenv import load_dotenv

load_dotenv()

CONFIG = {
  'ANTHROPIC_API_KEY': os.getenv("ANTHROPIC_API_KEY"),
  'PORT': int(os.getenv("PORT", 8080)),
  'BLOCK_RESOURCE_TYPES': [
    'beacon',
    'csp_report',
    'font',
    'image',
    'imageset',
    'media',
    'object',
    'texttrack',
  ],
  'BLOCK_RESOURCE_NAMES': [
    'adzerk',
    'analytics',
    'cdn.api.twitter',
    'doubleclick',
    'exelator',
    'facebook',
    'fontawesome',
    'google',
    'google-analytics',
    'googletagmanager',
  ]   
}



