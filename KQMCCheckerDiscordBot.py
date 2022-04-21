import requests
import base64
import json
import gzip
import zlib
import discord

import os

from KQMCChecker import check_config


def get_config_from_url(url:str):
    try:
        if "gcsim.app/viewer/share" in url:
            name = os.path.basename(url)
            url = "https://viewer.gcsim.workers.dev/" + name
            r= requests.get(url)
            raw_data:str = json.loads(r.content)['data']
            compressed = base64.b64decode(raw_data)
            try:
                data = gzip.decompress(compressed)
            except:
                data = zlib.decompress(compressed)
            data = json.loads(data)
            return data['config_file']
        return None
    except Exception as e:
        print(e)
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
    if content.lower().startswith("!kqmc"):
        split = content.split(maxsplit=2)
        if len(split) <= 1:
            await message.channel.send("Expected gcsim viewer link")
            return
        url = split[1]
        if not "gcsim.app/viewer/share" in url:
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
    if content.lower().startswith("!submit"):
        split = content.split(maxsplit=2)
        if len(split) <= 1:
            await message.channel.send("Expected gcsim viewer link")
            return
        url = split[1]
        if not "gcsim.app/viewer/share" in url:
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
        msg += "Config is being sent to DB maintainer"
        await message.channel.send(msg)
        if "is KQMC valid" in msg:
            kurt = await client.fetch_user(341979097414500377)
            if kurt is None:
                await message.channel.send("Kurt was not found")
                return
            if(len(split)>2):
                await kurt.send(f"<{url}>~{message.author.name}#{message.author.discriminator}~\n{split[2]}")
            else:
                await kurt.send(f"<{url}>~{message.author.name}#{message.author.discriminator}~")
            return
        return
client.run(TOKEN)