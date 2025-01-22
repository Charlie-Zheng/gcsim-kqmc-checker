A python script for checking if a GCSIM config adheres to KQMC standards. Also includes a Discord bot for easy integration into a Discord server.

# Requirements/Set up:
* python 3.9 or higher

To install the required python modules, run ```python -m pip install -r requirements.txt```

# Command Line arguments

`--glob` glob for files to check

`--debug` enables detailed debugging output

`--print-only-failures` print only when config fails to adhere to KQMC

`--kurt` [UNIMPLEMENTED] check for KurtC (C6 4*, C0 5*, R3 weapons)

## Example:

`python .\KQMCChecker.py .\config.txt` checks the file config.txt for KQMC stat standards

## Discord Bot:

This repository also includes a Discord bot that can check KQMC stat standards directly from a gcsim.app share link. 


### Running the Discord Bot:

The user needs to supply their own Discord token using the environment variable `DISCORD_TOKEN`.

On Windows, use `set DISCORD_TOKEN=[YOUR DISCORD TOKEN]` to set your token.

On Linux, use `export DISCORD_TOKEN=[YOUR DISCORD TOKEN]` to set your token.

Then, run `python .\KQMCCheckerDiscordBot.py` to start the bot.

### Interacting with the Discord Bot:

Message the Bot with a message with the format:
```
!kqmc https://gcsim.app/sh/MW7dPmpt9WPt
```

and the bot will respond

```
'MW7dPmpt9WPt' is KQMC valid
```

