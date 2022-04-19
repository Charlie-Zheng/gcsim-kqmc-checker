import requests
import base64
import json
import gzip
import discord

import os

from KQMCChecker import check_config


def get_config_from_url(url:str):
    try:
        url = url.replace("https://www.gcsim.app/viewer/share/", "https://viewer.gcsim.workers.dev/")
        r= requests.get(url)
        raw_data:str = json.loads(r.content)['data']
        compressed = base64.b64decode(raw_data)
        data = gzip.decompress(compressed)
        data = json.loads(data)
        return data['config_file']
    except:
        return None

TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    content:str = message.content
    if content.lower().startswith("!verifykqmc"):
        split = content.split(maxsplit=2)
        if len(split) <= 1:
            await message.channel.send("Expected gcsim viewer link")
            return
        url = split[1]
        if not url.startswith("https://www.gcsim.app/viewer/share/"):
            await message.channel.send("Expected gcsim viewer link")
            return
        if url[-1] == "/":
            url = url[:-1]
        config = get_config_from_url(url)
        if config is None:
            await message.channel.send("gcsim viewer link was invalid")
            return
        name = os.path.basename(url)
        msg = check_config(config, name)
        await message.channel.send(msg)
        return
client.run(TOKEN)