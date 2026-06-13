import random
import asyncio

import discord
from discord.ext import commands, tasks
from discord import app_commands

import lol_data


class LolCog(commands.GroupCog, name="lol", description="League of Legends profilok, rangok és statisztikák lekérdezése."):
    """A Discord cog handling League of Legends commands and background tasks.
    
    Manages account linking, rank fetching, and periodic updates the player database.
    Also used for fetching game data.
    """
    
    def __init__(self, bot: commands.Bot):
        """Initializes the LolCog and starts the background rank updater.

        Args:
            bot (commands.Bot): The main bot instance.
        """
        self.bot = bot
        self.lol_data = lol_data.LolData()
        self.background_rank_updater.start()
    
    def cog_unload(self):
        """Standard Cog method triggered when the extension is unloaded.
        
        Safely cancels the background task to prevent ghost loops.
        """
        self.background_rank_updater.cancel()

    @tasks.loop(minutes=1)
    async def background_rank_updater(self):
        """Background task that update player ranks.

        Iterates through the database, fetches new rank data via the Riot API
        on a separate thread, and saves the updated data.
        """
        print("Várakozás a Riot API-ra: Rangok frissítése a háttérben...")

        for discord_id in list(self.lol_data.account_database.keys()):
            try:
                account = self.lol_data.get_account_from_database(discord_id)
                await asyncio.to_thread(account.update_ranks)
                self.lol_data.account_database[discord_id] = account.to_dict()

            except Exception as e:
                print(f"Error updating ranks:\n```\n{e}\n```")

        self.lol_data.save_database()
        print("Frissítés kész.")

    @app_commands.command(name="random_champion", description="Megad egy random lol championt.")
    async def random_champion(self, interaction: discord.Interaction):
        """Selects and displays a random League of Legends champion.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.response.defer()

        # Generate a random champion.
        random_index = random.randint(0, len(self.lol_data.champion_names) - 1)
        champ_name, champ_img = self.lol_data.get_champion(random_index)
        
        # Create and send the embed.
        embed = discord.Embed(title=champ_name.upper())
        embed.set_image(url=champ_img)

        await interaction.followup.send(content=None, embed=embed)

    @app_commands.command(name="link_account", description="Linkeli a megadott lol fiókot a discord fiókodhoz")
    async def link_account(self, interaction: discord.Interaction, username: str, tag: str):
        """Links a user's Discord account to their League of Legends account.

        Args:
            interaction (discord.Interaction): The interaction object.
            username (str): The Riot Games username.
            tag (str): The Riot Games tag (without the #).
        """
        await interaction.response.defer(ephemeral=True)

        try:            
            await asyncio.to_thread(
                self.lol_data.add_account_to_database,
                interaction.user.id, 
                username, 
                tag
            )
            await interaction.followup.send(f"✅ Sikeresen linkelted a fiókod: **{username}#{tag}**!")

        except Exception as e:
            print(f"Error linking lol account:\n```\n{e}\n```")
            await interaction.followup.send("⚠️ Nem sikerült linkelni a fiókodat. Ellenőrizd a nevet és a taget!") 

    @app_commands.command(name="my_account", description="Visszaadja a te lol accountodat")
    async def my_account(self, interaction: discord.Interaction):
        """Fetches and displays the linked League of Legends account data of the user.

        Checks the database for the user and displays their stats.

        Args:
            interaction (discord.Interaction): The interaction object context.
        """
        await interaction.response.defer()

        try:     
            account = self.lol_data.get_account_from_database(interaction.user.id)
            
            # Check if account exists.
            if not account:
                await interaction.followup.send("⚠️ Még nem linkelted a fiókodat! Használd a `/lol link_account` parancsot.")
                return

            # Update the ranked data.
            await asyncio.to_thread(account.update_ranks)
            self.lol_data.account_database[str(interaction.user.id)] = account.to_dict()
            self.lol_data.save_database()
            
            # Fetch Summoner data.
            summoner = await asyncio.wait_for(
                asyncio.to_thread(
                    self.lol_data.watcher.summoner.by_puuid, 
                    self.lol_data.region, 
                    account.puuid
                ),
                timeout=10.0
            )

            # Format Rank strings.
            solo_string = self.__format_rank(account.solo_ranked)
            flex_string = self.__format_rank(account.flex_ranked)
            
            # Construct Final Embed.
            embed = self.__make_account_embed(
                member=interaction.user,
                username=account.username,
                tag=account.tag,
                level=summoner.get('summonerLevel', 0),
                icon_id=summoner.get('profileIconId', 1),
                solo_str=solo_string,
                flex_str=flex_string
            )

            await interaction.followup.send(embed=embed)

        except asyncio.TimeoutError:
            await interaction.followup.send("⚠️ A Riot szerverei jelenleg nem válaszolnak. Kérlek próbáld újra később!")
        except Exception as e:
            print(f"API Fetch Error in my_account:\n{e}")
            await interaction.followup.send("⚠️ Hiba történt a Riot szervereivel való kommunikáció során.")

    def __format_rank(self, rank_dict: dict) -> str:
        """Formats a rank dictionary into a readable string.

        Args:
            rank_dict (dict): Dictionary containing tier, rank, and lp data.

        Returns:
            str: A formatted rank string.
        """
        if rank_dict.get("tier") == "Unranked":
            return "Unranked"
        return f"{rank_dict['tier']} {rank_dict['rank']} ({rank_dict['lp']} LP)"
    
    def __make_account_embed(self, member: discord.Member, username: str, tag: str, 
                             level: int, icon_id: int, solo_str: str, flex_str: str) -> discord.Embed:
        """Constructs the visual embed for displaying a user's League of Legends profile.

        Args:
            member (discord.Member): The Discord member object.
            username (str): The Riot Games username.
            tag (str): The Riot Games tag.
            level (int): The current summoner level.
            icon_id (int): The ID of the profile icon.
            solo_str (str): The formatted Solo/Duo rank string.
            flex_str (str): The formatted Flex rank string.

        Returns:
            discord.Embed: The fully constructed embed ready to be sent.
        """
        # Profile icon
        game_version = self.lol_data.version
        icon_url = f"https://ddragon.leagueoflegends.com/cdn/{game_version}/img/profileicon/{icon_id}.png"

        # Embed base
        embed = discord.Embed(
            title=f"{username}#{tag}",
            color=discord.Color.blue(), 
        )
        
        # Discord avatar on top
        avatar_url = member.display_avatar.url if member.display_avatar else None
        embed.set_author(name=member.display_name, icon_url=avatar_url)
        
        # Set the profile icon
        embed.set_thumbnail(url=icon_url)
        
        # Level and Ranks
        embed.add_field(name="Szint", value=f"{level}", inline=False)
        embed.add_field(name="🏆 Solo/Duo", value=solo_str, inline=True)
        embed.add_field(name="🏆 Flex", value=flex_str, inline=True)
        
        return embed


async def setup(bot: commands.Bot):
    """Links the cog to the bot."""
    await bot.add_cog(LolCog(bot))