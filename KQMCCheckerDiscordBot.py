import requests
import base64
import json
import gzip
import zlib
import discord

import os

from KQMCChecker import check_json
from TotalStats import get_stats


def get_json_from_url(url: str):
    try:
        if "gcsim.app/sh/" in url or "gcsim.app/db/" in url:
            name = os.path.basename(url)
            url = "https://gcsim.app/api/share/" + \
                ("db/" if "gcsim.app/db/" in url else "") + name
            r = requests.get(url)
            data: str = json.loads(r.text)
            return data
        return None
    except Exception as e:
        print(e)
        return None


TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client(intents=discord.Intents.default())


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    content: str = message.content
    print(content)
    if content.lower().startswith("!kqmc"):
        split = content.split(maxsplit=2)
        if len(split) <= 1:
            await message.channel.send("Expected gcsim viewer link")
            return
        url = split[1]
        if "gcsim.app/sh/" not in url and "gcsim.app/db/" not in url:
            await message.channel.send("Expected gcsim viewer link")
            return
        if url[-1] == "/":
            url = url[:-1]
        data = get_json_from_url(url)
        if data is None:
            await message.channel.send("gcsim viewer link was invalid")
            return
        name = os.path.basename(url)
        msg = check_json(data, name)
        await message.channel.send(msg)
        return

client.run(TOKEN)
