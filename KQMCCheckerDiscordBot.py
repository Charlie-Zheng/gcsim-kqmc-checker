import requests
import json
import discord

import os

from KQMCChecker import check_json


def get_json_from_url(url: str):
    try:
        if "gcsim.app/sh/" in url or "gcsim.app/db/" in url:
            name = os.path.basename(url)
            new_url = "https://gcsim.app/api/share/"
            new_url += ("db/" if "gcsim.app/db/" in url else "")
            new_url += name
            print(new_url)
            r = requests.get(new_url)
            data: str = json.loads(r.text)
            return data
        return None
    except Exception as e:
        print(e)
        return None


client = discord.Client(intents=discord.Intents.default())


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    content: str = message.content
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

TOKEN = os.getenv('DISCORD_TOKEN')
client.run(TOKEN)
