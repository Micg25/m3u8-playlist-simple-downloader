import os
from urllib.parse import urljoin
import asyncio
import aiohttp
import ffmpeg
import time
# Limit the number of simultaneous downloads
MAX_CONCURRENT_DOWNLOADS = 30
semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Ho aggiunto 'session' tra gli argomenti perché altrimenti non veniva trovata
async def download_chunk(url_, session, progress, total_chunks):
    content = None
    
    # Riprova fino a 3 volte in caso di errore
    for attempt in range(3):
        try:
            async with semaphore:
                # CORREZIONE SINTASSI AIOHTTP
                async with session.get(url_, timeout=30, headers=headers) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        
                        progress[0] += 1
                        print(f"Progress: {progress[0]} / {total_chunks} chunks downloaded")
                        
                        # RESTITUIAMO il contenuto invece di scriverlo subito
                        # per evitare che i pezzi si mischino nel file
                        return content
                    else:
                        print(f"Failed to download chunk, status: {resp.status}")
        except Exception as e:
            print(f"Error downloading chunk (attempt {attempt+1}): {e}")
            await asyncio.sleep(2)
            
    return None # Se fallisce dopo i tentativi

async def main(url, name):
    print(f"Analyzing the playlist...: {url}")
    path_ts = "./video.ts"
    path_mp4 = f"./{name}" 
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as r:
                r.raise_for_status()
                text_content = await r.text()
                m3u8_content = text_content.splitlines()

            # Extracting .ts segments
            segments = []
            for line in m3u8_content:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                segment_url = urljoin(url, line)
                segments.append(segment_url)
            
            total_chunks = len(segments)
            print(f"{total_chunks} chunks found")

            progress = [0]
            
            # Creating tasks
            tasks = [download_chunk(seg, session, progress, total_chunks) for seg in segments]

            print("Downloading...")
            results = await asyncio.gather(*tasks)

            print("Creating .ts file...")
            with open(path_ts, "wb") as ts_file:
                for chunk_data in results:
                    if chunk_data:
                        ts_file.write(chunk_data)

            # Conversione
            print("CONVERTING TO MP4...")
            try:
                (
                    ffmpeg
                    .input(path_ts)
                    .output(path_mp4, codec='copy')
                    .run(overwrite_output=True)
                )
                print("CONVERSION COMPLETE")
                time.sleep(1)
                if os.path.exists(path_ts):
                    os.remove(path_ts)
            except ffmpeg.Error as e:
                print("ffmpeg ERROR", e)

        except Exception as e:
            print(f"\nError inside the main: {e}")

if __name__ == "__main__":
    link = input("Insert the .m3u8 url: ").strip()
    name = input("Insert the name: ").strip()
    
    if not name.endswith(".mp4"):
        name += ".mp4"
        
    asyncio.run(main(link, name))
