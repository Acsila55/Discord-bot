import discord
from discord.ext import commands

# Constants
LOG_CHANNEL_ID = 1512863571229409300 # bot-logs channel

class LoggingCog(commands.Cog, name="logging", description="A felhasználói interakciók és parancsok naplózása."):


    def __init__(self, bot: commands.Bot):
        """Initializes the LoggingCog.
        
        Args:
            bot (commands.Bot): The main bot instance.
        """
        self.bot = bot 

    def make_log_embed(self, interaction: discord.Interaction) -> discord.Embed:
        """Creates an embed object with the logging details

        Args:
            interaction (discord.Interaction): The interaction object containing the commands context.

        Returns:
            discord.Embed: A formatted embed with the logging details.
        """
        embed = discord.Embed(
            title="💻 Command Executed",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )

        # Add user and command data
        embed.add_field(name="User", value=interaction.user.mention, inline=True)
        embed.add_field(name="Command", value=f"`/{interaction.command.name}`", inline=True)
        
        # Add where command was called
        channel_name = interaction.channel.mention if interaction.channel else "Private Message"
        embed.add_field(name="Channel", value=channel_name, inline=True)

        return embed

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction): 
        """Event listener triggered when a user interacts with the bot.

        Logs all interactions to the specified log channel.

        Args:
            interaction (discord.Interaction): The interaction object containing the commands context.
        """
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID) 

        # Check if log channel is valid
        if log_channel is None:
            print("Logging channel has been deleted please restore it")
            return
        
        # Only listen for slash commands
        if interaction.type != discord.InteractionType.application_command:
            return
        
        # Log the command
        embed = self.make_log_embed(interaction)
        await log_channel.send(embed=embed)


import discord
from discord.ext import commands

# Constants
LOG_CHANNEL_ID = 1512863571229409300 # bot-logs chanel

class LoggingCog(commands.Cog):
    """A Discord Cog handling the logging of interactions with the bot"""

    def __init__(self, bot: commands.Bot):
        """Initializes the LoggingCog.
        
        Args:
            bot (commands.Bot): The main bot instance.
        """
        self.bot = bot 

    def make_log_embed(self, interaction: discord.Interaction) -> discord.Embed:
        """Creates an embed object with the logging details

        Args:
            interaction (discord.Interaction): The interaction context.

        Returns:
            discord.Embed: A formatted embed ready to be sent to the log channel.
        """
        embed = discord.Embed(
            title="💻 Command Executed",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )

        # Add user and command data
        embed.add_field(name="User", value=interaction.user.mention, inline=True)
        embed.add_field(name="Command", value=f"`/{interaction.command.name}`", inline=True)
        
        # Add where command was called
        channel_name = interaction.channel.mention if interaction.channel else "Private Message"
        embed.add_field(name="Channel", value=channel_name, inline=True)

        return embed

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction): 
        """Event listener triggered when a user interacts with the bot.

        Logs all interactions to the specified log channel.

        Args:
            interaction (discord.Interaction): The interaction object context.
        """
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID) 

        # Check if log channel is valid
        if log_channel is None:
            print("Logging channel has been deleted please restore it")
            return
        
        # Only listen for slash commands
        if interaction.type != discord.InteractionType.application_command:
            return
        
        # Log the command
        embed = self.make_log_embed(interaction)
        await log_channel.send(embed=embed)


async def setup(bot: commands.Bot):
    """Links the cog to the bot."""
    await bot.add_cog(LoggingCog(bot))