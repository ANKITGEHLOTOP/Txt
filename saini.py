import os
import re
import time
import mmap
import datetime
import aiohttp
import aiofiles
import asyncio
import logging
import requests
import tgcrypto
import subprocess
import concurrent.futures
from math import ceil
from utils import progress_bar
from pyrogram import Client, filters
from pyrogram.types import Message
from io import BytesIO
from pathlib import Path  
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

# Global variables
failed_counter = 0

def duration(filename):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
         "-of", "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

def get_mps_and_keys(api_url):
    response = requests.get(api_url)
    response.raise_for_status()
    response_json = response.json()
    return response_json.get('MPD'), response_json.get('KEYS')

def exec(cmd):
    process = subprocess.run(
        cmd, 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    output = process.stdout.decode()
    print(output)
    return output

def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        print("Waiting for tasks to complete")
        executor.map(exec, cmds)

async def aio_download(url, name, extension="pdf"):
    filename = f'{name}.{extension}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(filename, mode='wb') as f:
                    await f.write(await resp.read())
    return filename

async def pdf_download(url, file_name, chunk_size=1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    
    with requests.get(url, allow_redirects=True, stream=True) as r:
        r.raise_for_status()
        with open(file_name, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    fd.write(chunk)
    return file_name

def parse_vid_info(info):
    info = info.strip().split("\n")
    new_info = []
    temp = []
    
    for i in info:
        i = str(i).strip()
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            parts = i.split("|")[0].split(" ", 2)
            try:
                if len(parts) > 2 and "RESOLUTION" not in parts[2] and parts[2] not in temp and "audio" not in parts[2]:
                    temp.append(parts[2])
                    new_info.append((parts[0], parts[2]))
            except IndexError:
                pass
    return new_info

def vid_info(info):
    info = info.strip().split("\n")
    new_info = {}
    temp = []
    
    for i in info:
        i = str(i).strip()
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            parts = i.split("|")[0].split(" ", 3)
            try:
                if len(parts) > 2 and "RESOLUTION" not in parts[2] and parts[2] not in temp and "audio" not in parts[2]:
                    temp.append(parts[2])
                    new_info[parts[2]] = parts[0]
            except IndexError:
                pass
    return new_info

async def decrypt_and_merge_video(mpd_url, keys_string, output_path, output_name, quality="720"):
    try:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # Download video
        cmd1 = (
            f'yt-dlp -f "bv[height<={quality}]+ba/b" '
            f'-o "{output_path}/file.%(ext)s" '
            '--allow-unplayable-format --no-check-certificate '
            f'--external-downloader aria2c "{mpd_url}"'
        )
        print(f"Running command: {cmd1}")
        os.system(cmd1)
        
        # Process downloaded files
        avDir = list(output_path.iterdir())
        print(f"Downloaded files: {avDir}")
        print("Decrypting...")

        video_decrypted = False
        audio_decrypted = False

        for data in avDir:
            if data.suffix == ".mp4" and not video_decrypted:
                cmd2 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/video.mp4"'
                print(f"Running command: {cmd2}")
                os.system(cmd2)
                video_decrypted = (output_path / "video.mp4").exists()
                data.unlink()
            elif data.suffix == ".m4a" and not audio_decrypted:
                cmd3 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/audio.m4a"'
                print(f"Running command: {cmd3}")
                os.system(cmd3)
                audio_decrypted = (output_path / "audio.m4a").exists()
                data.unlink()

        if not video_decrypted or not audio_decrypted:
            raise FileNotFoundError("Decryption failed: video or audio file not found.")

        # Merge video and audio
        output_file = output_path / f"{output_name}.mp4"
        cmd4 = (
            f'ffmpeg -i "{output_path}/video.mp4" -i "{output_path}/audio.m4a" '
            f'-c copy "{output_file}"'
        )
        print(f"Running command: {cmd4}")
        os.system(cmd4)
        
        # Cleanup
        for f in [output_path / "video.mp4", output_path / "audio.m4a"]:
            if f.exists():
                f.unlink()

        if not output_file.exists():
            raise FileNotFoundError("Merged video file not found.")

        # Get duration info
        cmd5 = f'ffmpeg -i "{output_file}" 2>&1 | grep "Duration"'
        duration_info = os.popen(cmd5).read()
        print(f"Duration info: {duration_info}")

        return str(output_file)

    except Exception as e:
        print(f"Error during decryption and merging: {str(e)}")
        raise

async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if proc.returncode == 1:
        return False
    if stdout:
        return f'[stdout]\n{stdout.decode()}'
    if stderr:
        return f'[stderr]\n{stderr.decode()}'

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

def time_name():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H%M%S.mp4")

async def download_video(url, cmd, name, max_retries=10):
    global failed_counter
    download_cmd = (
        f'{cmd} -R 25 --fragment-retries 25 '
        '--external-downloader aria2c '
        '--downloader-args "aria2c: -x 16 -j 32"'
    )
    
    print(download_cmd)
    logging.info(download_cmd)
    
    while failed_counter <= max_retries:
        k = subprocess.run(download_cmd, shell=True)
        if "visionias" in cmd and k.returncode != 0:
            failed_counter += 1
            await asyncio.sleep(5)
            continue
        
        failed_counter = 0
        for ext in ["", ".webm", ".mkv", ".mp4", ".mp4.webm"]:
            file_path = name if not ext else f"{name.split('.')[0]}{ext}"
            if os.path.isfile(file_path):
                return file_path
        
        break
    
    return f"{name.split('.')[0]}.mp4"

def decrypt_file(file_path, key):  
    if not os.path.exists(file_path): 
        return False  

    with open(file_path, "r+b") as f:  
        num_bytes = min(28, os.path.getsize(file_path))  
        with mmap.mmap(f.fileno(), length=num_bytes, access=mmap.ACCESS_WRITE) as mmapped_file:  
            for i in range(num_bytes):  
                mmapped_file[i] ^= ord(key[i]) if i < len(key) else i 
    return True  

async def download_and_decrypt_video(url, cmd, name, key):  
    video_path = await download_video(url, cmd, name)  
    if video_path and decrypt_file(video_path, key):  
        print(f"File {video_path} decrypted successfully.")  
        return video_path  
    print(f"Failed to process {video_path}.")  
    return None  

async def send_doc(bot: Client, m: Message, cc, filename, cc1, prog, count, name, channel_id):
    reply = await bot.send_message(
        channel_id, 
        f"Downloading pdf:\n<pre><code>{name}</code></pre>"
    )
    await asyncio.sleep(1)
    
    try:
        await bot.send_document(channel_id, filename, caption=cc1)
        count += 1
    finally:
        await reply.delete()
        if os.path.exists(filename):
            os.remove(filename)
        await asyncio.sleep(3)

async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog, channel_id):
    # Generate thumbnail
    subprocess.run(
        f'ffmpeg -i "{filename}" -ss 00:00:10 -vframes 1 "{filename}.jpg"', 
        shell=True
    )
    await prog.delete()
    
    reply = await m.reply_text(f"<blockquote><b>Generate Thumbnail:</b></blockquote>\n{name}")
    
    try:
        thumbnail = f"{filename}.jpg" if thumb == "/d" else thumb
        dur = int(duration(filename))
        start_time = time.time()

        try:
            await bot.send_video(
                channel_id,
                filename,
                caption=cc,
                supports_streaming=True,
                height=720,
                width=1280,
                thumb=thumbnail,
                duration=dur,
                progress=progress_bar,
                progress_args=(reply, start_time)
        except Exception as e:
            await bot.send_document(
                channel_id,
                filename,
                caption=cc,
                progress=progress_bar,
                progress_args=(reply, start_time))
    except Exception as e:
        await m.reply_text(f"Error: {str(e)}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(f"{filename}.jpg"):
            os.remove(f"{filename}.jpg")
        await reply.delete()
