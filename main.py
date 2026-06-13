import os

import discord
from discord.ext import commands
from dotenv import load_dotenv


class AtlasBot(commands.Bot):
    """The main bot class, inherits from commands.Bot.
    
    This class handles the intial bot setup and event listeners.
    """
    def __init__(self):
        """Initializes the bot with default intents, status, activity.

        Also defines the list of cogs to be loaded during startup.
        """
        super().__init__(
            command_prefix="!",  # Prefix for legacy commands (Not used)
            intents=discord.Intents.all(),  # Permissions (Currently all)
            case_insensitive=True,  # Ignores casing for legacy commands
            activity=discord.CustomActivity(name="Just Gooning"),  # Initial activity
            status=discord.Status.online  # Initial online presence status
        )

        # List of extension modules (cogs)
        self.cogs_list = [
            "cogs.logging",
            "cogs.admin",
            "cogs.lol",
            "cogs.general",
        ]
    
    async def setup_hook(self): 
        """Setup function that initialises the bot behaviour.

        Loads extensions (cogs) and slash commands.
        """
        print("Loading Bot Commands...")
        
        # Loads the defined extensions.
        for cog in self.cogs_list:
            await self.load_extension(cog)
            print(f" -> Loaded {cog}")
        
        # Syncs the slash commands with discord.
        await self.tree.sync() 

        print("Bot Commands Loaded & Synced!")

    async def on_ready(self):
        """Event listener triggered when the bot is ready."""
        print("Atlas is online!")


if __name__ == "__main__":
    # Validate Token
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN not found.")

    # Run Bot
    bot = AtlasBot()
    bot.run(TOKEN)