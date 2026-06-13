

'''
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def get_rank(name: str, tag: str, region: str = "eune") -> dict[str, str]:
    """
    Get LoL rank from OP.GG.
    Returns a dict: {"Solo": ..., "Flex": ...}
    """

    name_encoded = quote(name)
    tag_encoded = quote(tag)
    headers = {"User-Agent": "Mozilla/5.0"}

    ranks = {}
    for queue in ["SOLORANKED", "FLEXRANKED"]:
        url = f"https://op.gg/lol/summoners/{region}/{name_encoded}-{tag_encoded}?queue_type={queue}"
        resp = requests.get(url, headers=headers)

        if resp.status_code == 404:
            ranks[queue[:4]] = "404"
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        rank_tag = soup.find("strong", class_="text-xl first-letter:uppercase")
        ranks[queue[:4]] = rank_tag.text.strip() if rank_tag else "unranked"

    return {"Solo": ranks["SOLA"], "Flex": ranks["FLEX"]}

'''

import requests
from bs4 import BeautifulSoup


def get_rank(name : str,tag : str,region : str = "eune",) -> dict[str]:
    """
    Get rank from OP.GG first one is solo-duo, second flex
    """

    name = name.replace(" ","%20")
    resp = requests.get(f'https://op.gg/lol/summoners/{region}/{name}-{tag}?queue_type=SOLORANKED')
    if str(resp) == "<Response [404]>":
        return {"ERROR": resp}
        
    soup = BeautifulSoup(resp.text,'html.parser')

    soup = soup.find("strong",class_ = "text-xl first-letter:uppercase") 
    try:
        solo = soup.string
    except Exception:
        solo = "unranked"
    
    resp = requests.get(f'https://op.gg/lol/summoners/{region}/{name}-{tag}?queue_type=FLEXRANKED').text
    soup = BeautifulSoup(resp,'html.parser')   
    soup = soup.find("strong",class_ = "text-xl first-letter:uppercase")    
    try:
        flex = soup.string
    except Exception:
        flex = "unranked"


    return {"Solo" : solo, "Flex" : flex}


def best_champ(name : str,tag : str,region : str = "eune",) -> str:
    """
    returns the players champion with the highest mastery point
    """
    name = name.replace(" ","%20")
    resp = requests.get(f'https://op.gg/lol/summoners/{region}/{name}-{tag}?queue_type=SOLORANKED').text
    soup = BeautifulSoup(resp,'html.parser')
    soup = soup.find("span",class_ = "inline-block w-full overflow-hidden text-ellipsis whitespace-nowrap pt-2 text-center text-xs font-bold text-gray-900") 
    return soup.string