import json
import os
from typing import Optional, Dict, Any, Tuple, List

from dotenv import load_dotenv
from riotwatcher import LolWatcher, RiotWatcher

load_dotenv()


class LolAccount:
    """Represents a linked League of Legends account with cached rank data."""

    def __init__(
        self, 
        watcher: LolWatcher, 
        region: str, 
        discord_id: str, 
        username: str, 
        tag: str, 
        puuid: str,
        solo_ranked: Optional[Dict[str, Any]] = None, 
        solo_ranked_score: int = -1, 
        flex_ranked: Optional[Dict[str, Any]] = None, 
        flex_ranked_score: int = -1
    ):
        """Initializes a League of Legends account object.

        Args:
            watcher (LolWatcher): The Riot API watcher instance.
            region (str): The server region (e.g., 'eun1').
            discord_id (str): The linked Discord user ID.
            username (str): The Riot Games username.
            tag (str): The Riot Games tag.
            puuid (str): The unique Riot PUUID.
            solo_ranked (dict, optional): Cached solo rank data.
            solo_ranked_score (int, optional): Cached solo rank numerical score.
            flex_ranked (dict, optional): Cached flex rank data.
            flex_ranked_score (int, optional): Cached flex rank numerical score.
        """
        # Riot API
        self.watcher = watcher
        self.region = region

        # Discord Account
        self.discord_id = discord_id

        # LoL Account
        self.username = username
        self.tag = tag
        self.puuid = puuid
        self._summoner_id = None 

        # LoL Rank Defaults
        self.solo_ranked = solo_ranked or {"tier": "Unranked", "rank": "", "lp": 0}
        self.solo_ranked_score = solo_ranked_score

        self.flex_ranked = flex_ranked or {"tier": "Unranked", "rank": "", "lp": 0}
        self.flex_ranked_score = flex_ranked_score

    @property
    def summoner_id(self) -> str:
        """Fetches the summoner ID from the Riot API (only when needed)."""
        if self._summoner_id is None:
            data = self.watcher.summoner.by_puuid(self.region, self.puuid)
            self._summoner_id = data.get('id')
        return self._summoner_id

    def get_ranks(self) -> Dict[str, Dict[str, Any]]:
        """Fetches current rank data from the Riot API.

        Returns:
            dict: A dictionary containing 'Solo' and 'Flex' rank dictionaries.
        """
        ranks = {
            "Solo": {"tier": "Unranked", "rank": "", "lp": 0},
            "Flex": {"tier": "Unranked", "rank": "", "lp": 0}
        }
        
        if not self.summoner_id:
            return ranks
        
        try:
            ranked_data = self.watcher.league.by_summoner(self.region, self.summoner_id)
            
            for queue in ranked_data:
                tier = queue.get('tier', 'Unknown').capitalize()
                rank = queue.get('rank', '')              
                lp = queue.get('leaguePoints', 0)
                rank_dict = {"tier": tier, "rank": rank, "lp": lp}
                
                if queue.get('queueType') == 'RANKED_SOLO_5x5':
                    ranks["Solo"] = rank_dict
                elif queue.get('queueType') == 'RANKED_FLEX_SR':
                    ranks["Flex"] = rank_dict
                    
        except Exception as e:
            print(f"Rank API Error for {self.username}: {e}")
            
        return ranks
    
    def calculate_rank_score(self, tier: str, rank: str, lp: int) -> int:
        """Calculates the total lp score from the rank data.

        Args:
            tier (str): The rank tier (e.g., 'Gold').
            rank (str): The rank division (e.g., 'IV').
            lp (int): The current league points.

        Returns:
            int: The calculated numerical score, or -1 if unranked.
        """
        # Rank tiers
        tiers = {
            "Unranked": -1,
            "Iron": 0,
            "Bronze": 400,
            "Silver": 800,
            "Gold": 1200,
            "Platinum": 1600,
            "Emerald": 2000,
            "Diamond": 2400,
            "Master": 2800, 
            "Grandmaster": 2800,
            "Challenger": 2800 
        }
        
        # Divisions
        divisions = {"IV": 0, "III": 100, "II": 200, "I": 300, "": 0}
        
        tier_score = tiers.get(tier.capitalize(), -1)

        # Unranked players rank score is -1.
        if tier_score == -1:
            return -1 
            
        div_score = divisions.get(rank.upper(), 0)
        
        return tier_score + div_score + lp
    
    def update_ranks(self):
        """Fetches fresh ranks from the API and recalculates internal scores."""
        ranks = self.get_ranks()
        self.solo_ranked = ranks["Solo"]
        self.flex_ranked = ranks["Flex"]

        self.solo_ranked_score = self.calculate_rank_score(
            self.solo_ranked["tier"], self.solo_ranked["rank"], self.solo_ranked["lp"]
        )
        self.flex_ranked_score = self.calculate_rank_score(
            self.flex_ranked["tier"], self.flex_ranked["rank"], self.flex_ranked["lp"]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the account object to a dictionary for JSON storage.

        Returns:
            dict: The serialized account data.
        """
        return {
            "username": self.username,
            "tag": self.tag,
            "puuid": self.puuid,
            "solo_ranked": self.solo_ranked,
            "solo_ranked_score": self.solo_ranked_score,
            "flex_ranked": self.flex_ranked,
            "flex_ranked_score": self.flex_ranked_score,
        }


class LolData:
    """Manages the Riot API usage, and the local user database."""

    def __init__(self):
        """Initializes the LolData manager."""
        # Riot API
        api_key = os.getenv('RIOT_API_KEY')
        self.watcher = LolWatcher(api_key)
        self.riot_watcher = RiotWatcher(api_key)

        self.region = "eun1"
        self.routing = "europe"

        # LoL data
        self.version = self.watcher.data_dragon.versions_for_region("eune")['n']['champion']
        self.champion_names = self.__load_champ_names()

        # Discord user database
        self.database_file = "lol_accounts.json"
        self.account_database = self.__load_account_database()
            
    def add_account_to_database(self, discord_id: int, lol_name: str, lol_tag: str):
        """Fetches a Riot account and saves it to the local JSON database.

        Args:
            discord_id (int): The Discord user's ID.
            lol_name (str): The Riot Games username.
            lol_tag (str): The Riot Games tag.
        """
        riot_account = self.riot_watcher.account.by_riot_id(self.routing, lol_name, lol_tag)
        
        account = LolAccount(
            watcher=self.watcher, 
            region=self.region, 
            discord_id=str(discord_id), 
            username=lol_name, 
            tag=lol_tag, 
            puuid=riot_account["puuid"]
        )
        
        account.update_ranks()

        # Save to database
        self.account_database[str(discord_id)] = account.to_dict()
        self.save_database()

    def get_account_from_database(self, discord_id: int) -> Optional[LolAccount]:
        """Retrieves a LolAccount object from the database if it exists.

        Args:
            discord_id (int): The Discord user's ID.

        Returns:
            LolAccount or None: The instantiated account object, or None if not found.
        """
        user_data = self.account_database.get(str(discord_id))
        
        if user_data:
            return LolAccount(
                watcher=self.watcher,
                region=self.region,
                discord_id=str(discord_id),
                username=user_data["username"],
                tag=user_data["tag"],
                puuid=user_data["puuid"],
                solo_ranked=user_data["solo_ranked"],
                solo_ranked_score=user_data["solo_ranked_score"],
                flex_ranked=user_data["flex_ranked"],
                flex_ranked_score=user_data["flex_ranked_score"]
            )
        return None

    def save_database(self):
        """Writes the current state of the account database to the JSON file."""
        with open(self.database_file, "w", encoding="utf-8") as f: 
            json.dump(self.account_database, f, indent=4)

    def get_champion_icon(self, name: str) -> str:
        """Constructs the Data Dragon URL for a champion's profile icon.

        Args:
            name (str): The name of the champion.

        Returns:
            str: The image URL.
        """
        if name not in self.champion_names:
            return ""
            
        champ_id = name.replace(" ", "").replace("'", "").capitalize()
        if name == "Wukong": 
            champ_id = "MonkeyKing"  # Wukong is weird
        
        return f"http://ddragon.leagueoflegends.com/cdn/{self.version}/img/champion/{champ_id}.png"
        
    def get_champion(self, index: int) -> Tuple[str, str]:
        """Fetches a champion's name and icon URL by index.

        Args:
            index (int): The list index.

        Returns:
            tuple: A tuple containing (champion_name, icon_url).
        """
        index = index % len(self.champion_names) 
        name = self.champion_names[index]
        icon = self.get_champion_icon(name)
        return name, icon

    def __load_champ_names(self) -> List[str]:
        """Fetches the latest list of champion names from Data Dragon.

        Returns:
            list: A list of champion name strings.
        """
        print("Fetching latest Champion Data from Riot...")
        champs = self.watcher.data_dragon.champions(self.version, full=False)['data']
        names = [champs[key]['name'] for key in champs]
        print(f"✅ Loaded {len(names)} champions!")
        return names

    def __load_account_database(self) -> Dict[str, Any]:
        """Loads the local JSON database from disk.

        Returns:
            dict: The dictionary representation of the JSON file.
        """
        if os.path.exists(self.database_file):
            with open(self.database_file, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print(f"⚠️ Warning: {self.database_file} is corrupted or empty!")
        return {}