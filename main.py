import os
import re
import sys
import m3u8
import json
import time
import pytz
import asyncio
import requests
import subprocess
import urllib
import urllib.parse
import yt_dlp
import tgcrypto
import cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64encode, b64decode
from logs import logging
from bs4 import BeautifulSoup
import saini as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN, OWNER, CREDIT, AUTH_USERS
from aiohttp import ClientSession
from subprocess import getstatusoutput
from pytube import YouTube
from aiohttp import web
import random
from pyromod import listen
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import aiofiles
import zipfile
import shutil
import ffmpeg

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

cookies_file_path = os.getenv("cookies_file_path", "youtube_cookies.txt")
api_url = "http://master-api-v3.vercel.app/"
api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzkxOTMzNDE5NSIsInRnX3VzZXJuYW1lIjoi4p61IFtvZmZsaW5lXSIsImlhdCI6MTczODY5MjA3N30.SXzZ1MZcvMp5sGESj0hBKSghhxJ3k1GTWoBUbivUe1I"
token_cp ='eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9r'
adda_token = "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJkcGthNTQ3MEBnbWFpbC5jb20iLCJhdWQiOiIxNzg2OTYwNSIsImlhdCI6MTc0NDk0NDQ2NCwiaXNzIjoiYWRkYTI0Ny5jb20iLCJuYW1lIjoiZHBrYSIsImVtYWlsIjoiZHBrYTU0NzBAZ21haWwuY29tIiwicGhvbmUiOiI3MzUyNDA0MTc2IiwidXNlcklkIjoiYWRkYS52MS41NzMyNmRmODVkZDkxZDRiNDkxN2FiZDExN2IwN2ZjOCIsImxvZ2luQXBpVmVyc2lvbiI6MX0.0QOuYFMkCEdVmwMVIPeETa6Kxr70zEslWOIAfC_ylhbku76nDcaBoNVvqN4HivWNwlyT0jkUKjWxZ8AbdorMLg"
photologo = 'https://tinypic.host/images/2025/02/07/DeWatermark.ai_1738952933236-1.png'
photoyt = 'https://tinypic.host/images/2025/03/18/YouTube-Logo.wine.png'
photocp = 'https://tinypic.host/images/2025/03/28/IMG_20250328_133126.jpg'
photozip = 'https://envs.sh/cD_.jpg'

# Inline keyboard for start command
BUTTONSCONTACT = InlineKeyboardMarkup([[InlineKeyboardButton(text="📞 Contact", url="https://t.me/SHINING_STAR_OP")]])
keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="🛠️ Help", url="https://t.me/SHINING_STAR_OP"),
            InlineKeyboardButton(text="🛠️ Repo", url="https://T.ME/SHINING_STAR_OP"),
        ],
    ]
)

# Image URLs for the random image feature
image_urls = [
    "https://tinypic.host/images/2025/02/07/IMG_20250207_224444_975.jpg",
    "https://tinypic.host/images/2025/02/07/DeWatermark.ai_1738952933236-1.png",
]

# --- FIXED CLASS PLUS DRM HANDLING ---
def get_classplus_drm_content(url):
    """Handle Classplus DRM content with multiple fallback methods"""
    try:
        # Method 1: Direct API call
        headers = {'x-access-token': token_cp, "X-CDN-Tag": "empty"}
        api_url = f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}'
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()['url'], None
        
        # Method 2: Alternative API endpoint
        alt_api = f'https://classplus-dl.vercel.app/api?url={url}'
        alt_response = requests.get(alt_api)
        
        if alt_response.status_code == 200:
            data = alt_response.json()
            return data.get('mpd_url'), data.get('keys')
            
    except Exception as e:
        logging.error(f"Classplus DRM error: {str(e)}")
    
    return url, None

# --- MODIFIED DRM HANDLER ---
@bot.on_message(filters.command(["drm"]) )
async def txt_handler(bot: Client, m: Message):  
    # ... [previous code until DRM handling] ...

    try:    
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        
        links = []
        for i in content:
            if "://" in i:
                url = i.split("://", 1)[1]
                links.append(i.split("://", 1))
                # ... [file type counting] ...
        os.remove(x)
    except:
        # ... [error handling] ...

    # ... [user input collection] ...

    try:
        for i in range(arg-1, len(links)):
            Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + Vxy
            link0 = "https://" + Vxy

            # ... [name processing] ...

            # === FIXED CLASS PLUS HANDLING ===
            if "classplusapp.com/drm/" in url or "media-cdn.classplusapp.com/drm/" in url:
                url, keys_data = get_classplus_drm_content(url)
                if keys_data:
                    keys_string = " ".join([f"--key {key}" for key in keys_data])
                else:
                    keys_string = ""

            # ... [other platform handling] ...

            # === MODIFIED DOWNLOAD LOGIC ===
            if 'drmcdni' in url or 'drm/wv' in url or ("classplusapp.com" in url and keys_string):
                Show = f"<i><b>Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
                res_file = await helper.decrypt_and_merge_video(url, keys_string, path, name, raw_text2)
                filename = res_file
                await prog.delete(True)
                await helper.send_vid(bot, m, cc, filename, thumb, name, prog, channel_id)
                count += 1
                await asyncio.sleep(1)
                continue

            # ... [other download methods] ...

    except Exception as e:
        # ... [error handling] ...

    # ... [completion message] ...

# --- MODIFIED TEXT HANDLER ---
@bot.on_message(filters.text & filters.private)
async def text_handler(bot: Client, m: Message):
    # ... [previous code] ...

    try:
            Vxy = link.replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = Vxy

            # ... [name processing] ...

            # === FIXED CLASS PLUS HANDLING ===
            if "classplusapp.com/drm/" in url or "media-cdn.classplusapp.com/drm/" in url:
                url, keys_data = get_classplus_drm_content(url)
                if keys_data:
                    keys_string = " ".join([f"--key {key}" for key in keys_data])
                else:
                    keys_string = ""

            # ... [other platform handling] ...

            # === MODIFIED DOWNLOAD LOGIC ===
            if 'drmcdni' in url or 'drm/wv' in url or ("classplusapp.com" in url and keys_string):
                Show = f"**⚡Dᴏᴡɴʟᴏᴀᴅɪɴɢ Sᴛᴀʀᴛᴇᴅ...⏳**\n" \
                       f"🔗𝐋𝐢𝐧𝐤 » {url}\n" \
                       f"✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ {CREDIT}"
                prog = await m.reply_text(Show, disable_web_page_preview=True)
                res_file = await helper.decrypt_and_merge_video(url, keys_string, path, name, raw_text2)
                filename = res_file
                await prog.delete(True)
                await helper.send_vid(bot, m, cc, filename, thumb, name, prog, channel_id)
                await asyncio.sleep(1)
                pass

            # ... [other download methods] ...

    except Exception as e:
        # ... [error handling] ...

# ... [rest of the bot code] ...

bot.run()
