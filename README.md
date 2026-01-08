A simple python script that allows you to download the content of an m3u8 playlist. It's been made using asyncio and aiohttp allowing fast async network calls.

DEPENDENCIES:
pip install aiohttp ffmpeg-python requests
HOW TO USE IT:
1. Download the .py file and add it in a folder
2. Modify the "MAX_CONCURRENT_DOWNLOADS" variable as you wish, by default is set to 30 concurrent requests
3. Run the script, insert m3u8 url and file name when asked 
