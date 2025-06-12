import os
import sys
import time
import json
import logging
import requests
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ---------------------------- #
# Configuration & Constants
# ---------------------------- #

# Telegram API credentials - Set these as environment variables or replace directly here
API_ID = int(os.getenv("API_ID", "123456"))        # Replace with your API_ID
API_HASH = os.getenv("API_HASH", "your_api_hash")  # Replace with your API_HASH
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")  # Replace with your bot token

# Classplus token or other API tokens if needed
CLASSPLUS_TOKEN = os.getenv("CLASSPLUS_TOKEN", "your_classplus_token")

# Logger setup
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inline Keyboard Buttons
CONTACT_BUTTON = InlineKeyboardMarkup(
    [[InlineKeyboardButton("📞 Contact", url="https://t.me/SHINING_STAR_OP")]]
)
HELP_REPO_BUTTON = InlineKeyboardMarkup(
    [[
        InlineKeyboardButton("🛠️ Help", url="https://t.me/SHINING_STAR_OP"),
        InlineKeyboardButton("🛠️ Repo", url="https://t.me/SHINING_STAR_OP")
    ]]
)


# ---------------------------- #
# Helper Functions
# ---------------------------- #

def get_classplus_drm_url_and_keys(url, max_retries=3):
    """
    Try multiple APIs/endpoints to get the actual playable URL and keys needed to download DRM-protected content.
    Returns tuple (playable_url, keys_dict or None)
    """
    try:
        headers = {
            'x-access-token': CLASSPLUS_TOKEN,
            'User-Agent': 'Mobile-Android',
            'app-version': '1.4.37.1',
            'api-version': '18',
            'device-id': '5d0d17ac8b3c9f51'
        }

        fallback_endpoints = [
            f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}',
            f'https://classplus-dl.vercel.app/api?url={url}',
            f'https://dragoapi.vercel.app/classplus?link={url}',
        ]

        for retry in range(max_retries):
            for api_url in fallback_endpoints:
                try:
                    logger.info(f"Trying DRM API: {api_url}")
                    resp = requests.get(api_url, headers=headers if 'classplusapp' in api_url else {})
                    if resp.status_code == 200:
                        data = resp.json()
                        # Try to parse different response structures
                        playable_url = data.get("url") or data.get("mpd_url") or url
                        keys = data.get("keys")  # Can be None
                        logger.info(f"Received playable URL: {playable_url}")
                        return playable_url, keys
                    else:
                        logger.warning(f"DRM API {api_url} returned status {resp.status_code}")
                except Exception as e:
                    logger.error(f"Error connecting to DRM API {api_url}: {str(e)}")
            time.sleep(2)
        logger.error("All DRM API attempts failed")
    except Exception as err:
        logger.error(f"Exception in get_classplus_drm_url_and_keys: {err}")

    # Fallback: return original URL with no keys
    return url, None


def download_with_yt_dlp(url: str, output_file: str, quality: str = "720", drm_keys: dict = None) -> bool:
    """
    Downloads the video via yt-dlp with optional DRM keys and quality restrictions.
    Returns True if download succeeded, False otherwise.
    """
    try:
        ytdlp_cmd = [
            "yt-dlp",
            "--allow-unplayable-formats",  # for DRM content sometimes needed
            "-f", f"best[height<={quality}]",
            "-o", output_file,
        ]

        # If DRM keys exist, append external downloader args with decryption key(s)
        if drm_keys:
            # Example key format assumed here; adjust if API returns keys differently
            key_str = ",".join(drm_keys.values()) if isinstance(drm_keys, dict) else drm_keys
            # Note: yt-dlp supports --external-downloader-args for ffmpeg
            ytdlp_cmd.extend([
                "--external-downloader", "ffmpeg",
                "--external-downloader-args", f"-decryption_key {key_str}"
            ])

        ytdlp_cmd.append(url)

        logger.info(f"Running yt-dlp command: {' '.join(ytdlp_cmd)}")

        # Execute and wait for completion
        completed = subprocess.run(ytdlp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if completed.returncode == 0:
            logger.info(f"Download succeeded: {output_file}")
            return True
        else:
            logger.error(f"yt-dlp failed with code {completed.returncode}:\n{completed.stderr}")
            return False

    except Exception as e:
        logger.error(f"Exception in download_with_yt_dlp: {e}")
        return False


# ---------------------------- #
# Bot Commands and Handlers
# ---------------------------- #

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "Hello! I am your DRM-capable downloader bot.\n"
        "Send /help to know more.",
        reply_markup=CONTACT_BUTTON
    )


@app.on_message(filters.command("help"))
async def help_handler(client: Client, message: Message):
    await message.reply_text(
        "Usage:\n"
        "/drm - Send a text file containing one or more Classplus or other links to download DRM-protected or regular videos.\n"
        "You'll be asked to provide preferred video quality.\n\n"
        "Support and Repo links:",
        reply_markup=HELP_REPO_BUTTON
    )


@app.on_message(filters.command("drm"))
async def drm_download_handler(client: Client, message: Message):
    """
    Expects user to send a text file with video links. For each link:
    - Detects if it's Classplus DRM protected content.
    - Fetches proper playable URL and DRM keys if possible.
    - Downloads using yt-dlp with optional DRM key usage.
    """
    try:
        await message.reply_text("Please upload your text file containing video links (one link per line).")
        input_file_msg: Message = await client.listen(message.chat.id, timeout=120)

        if not input_file_msg.document:
            await message.reply_text("You did not send a valid document file. Please try again.")
            return

        # Download user uploaded file locally
        file_path = await input_file_msg.download()
        logger.info(f"Downloaded user file: {file_path}")

        # Read links from file
        with open(file_path, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]

        os.remove(file_path)

        if not links:
            await message.reply_text("File is empty or no valid links found!")
            return

        # Ask user for preferred quality
        quality_msg = await message.reply_text(
            "Please send preferred download quality (e.g. 360, 480, 720, 1080). Default is 720."
        )
        try:
            quality_resp: Message = await client.listen(message.chat.id, timeout=30)
            quality = quality_resp.text if quality_resp.text.isdigit() else "720"
        except Exception:
            quality = "720"

        await quality_msg.delete()

        for link in links:
            # Basic sanity check
            if not (link.startswith("http://") or link.startswith("https://")):
                await message.reply_text(f"Skipping invalid URL: {link}")
                continue

            await message.reply_text(f"Processing link: {link}")

            # Detect Classplus links for DRM processing
            if "classplusapp.com/drm" in link or "media-cdn.classplusapp.com" in link:
                playable_url, drm_keys = get_classplus_drm_url_and_keys(link)

                output_filename = f"output_{int(time.time())}.mp4"
                success = download_with_yt_dlp(playable_url, output_filename, quality, drm_keys)

                if success and os.path.exists(output_filename):
                    # Send the video file
                    await client.send_document(message.chat.id, output_filename, caption=f"Downloaded: {link}")
                    os.remove(output_filename)
                else:
                    await message.reply_text(f"Failed to download DRM video: {link}")
            else:
                # Non-DRM normal yt-dlp download
                output_filename = f"output_{int(time.time())}.mp4"
                success = download_with_yt_dlp(link, output_filename, quality)

                if success and os.path.exists(output_filename):
                    await client.send_document(message.chat.id, output_filename, caption=f"Downloaded: {link}")
                    os.remove(output_filename)
                else:
                    await message.reply_text(f"Failed to download video: {link}")

    except Exception as e:
        logger.error(f"Exception in drm_download_handler: {e}")
        await message.reply_text(f"An error occurred: {e}")


@app.on_message(filters.command("ping"))
async def ping_handler(client: Client, message: Message):
    await message.reply_text("Pong!")


# ---------------------------- #
# Run Bot
# ---------------------------- #
if __name__ == "__main__":
    if not all([API_ID, API_HASH, BOT_TOKEN]):
        logger.error("Please set API_ID, API_HASH and BOT_TOKEN environment variables correctly!")
        sys.exit(1)

    logger.info("Starting bot...")
    app.run()
