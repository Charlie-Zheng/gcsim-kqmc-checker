import requests
import json
from discord import Client, Intents, Interaction, app_commands
from discord.app_commands import AppCommandContext, AppInstallationType, CommandTree
import os

from KQMCChecker import check_json


def get_json_from_url(url: str):
    try:
        if url.startswith("https://gcsim.app/sh/") or url.startswith("https://gcsim.app/db/"):
            name = os.path.basename(url)
            new_url = "https://gcsim.app/api/share/"
            new_url += ("db/" if url.startswith("https://gcsim.app/db/") else "")
            new_url += name
            r = requests.get(new_url)
            data: str = json.loads(r.text)
            return data
        return None
    except Exception as e:
        print(e)
        return None


client = Client(intents=Intents.default())

tree = CommandTree(client)


@client.event
async def on_ready():
    commands = await tree.sync()
    command_names = [c.name for c in commands]
    print(f'{client.user} has connected to Discord! Available commands: {command_names}')


@tree.command(name="kqmc", description="Checks a gcsim share link for KQMC artifact stats compliance")
async def kqmc(interaction: Interaction, link: str):
    """Checks a gcsim share link for KQMC artifact stats compliance
    Args:
        interaction (discord.Interaction): the interaction that invokes this coroutine
        link (str): gcsim link to check
    """
    url = link
    if not url.startswith("https://gcsim.app/sh/") and not url.startswith("https://gcsim.app/db/"):
        await interaction.response.send_message("Expected gcsim viewer link")
        return
    if url[-1] == "/":
        url = url[:-1]
    data = get_json_from_url(url)
    if data is None:
        await interaction.response.send_message("gcsim viewer link was invalid")
        return
    msg = check_json(data, url)
    await interaction.response.send_message(msg)

TOKEN = os.getenv('DISCORD_TOKEN')
client.run(TOKEN)
