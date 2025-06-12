#🇳‌🇮‌🇰‌🇭‌🇮‌🇱‌
# Add your details here and then deploy by clicking on HEROKU Deploy button
import os
from os import environ

API_ID = int(environ.get("API_ID", "29905645"))
API_HASH = environ.get("API_HASH", "e5a701f6e0b5fb659cb57a230b9a3feb")
BOT_TOKEN = environ.get("BOT_TOKEN", "7938240034:AAHzPr4fzIEmDIH5c9UJz2bC9bhbvR5SZtg")
OWNER = int(environ.get("OWNER", "6743675415"))
CREDIT = "JANKI"
AUTH_USER = os.environ.get('AUTH_USERS', '6743675415').split(',')
AUTH_USERS = [int(user_id) for user_id in AUTH_USER]
if int(OWNER) not in AUTH_USERS:
    AUTH_USERS.append(int(OWNER))
  
#WEBHOOK = True  # Don't change this
#PORT = int(os.environ.get("PORT", 8080))  # Default to 8000 if not set
