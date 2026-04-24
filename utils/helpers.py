import re
import time
from typing import Optional
from ..data import get_player_data, schedule_save
from ..constants import SLANG_MAP

def niggifier(text: str) -> str:
    """Convert text to hood slang (enhanced)."""
    words = text.split()
    transformed = []
    for word in words:
        match = re.match(r"([^\w]*)([\w']+)([^\w]*)", word)
        if match:
            prefix, clean, suffix = match.groups()
            lower_clean = clean.lower()
            if lower_clean in SLANG_MAP:
                transformed.append(prefix + SLANG_MAP[lower_clean].upper() + suffix)
            else:
                transformed.append(word)
        else:
            transformed.append(word)
    return " ".join(transformed)

def get_street_rank(bread: int, street_cred: int) -> dict:
    """Get street rank based on total bread and street cred."""
    total = bread + (street_cred * 100)
    if total > 1_000_000:
        return {"name": "💎 Kingpin", "cdMult": 0.5, "level": 5}
    if total > 500_000:
        return {"name": "🔥 Boss", "cdMult": 0.7, "level": 4}
    if total > 100_000:
        return {"name": "💸 Hustler", "cdMult": 0.85, "level": 3}
    if total > 50_000:
        return {"name": "📍 Corner Kid", "cdMult": 0.95, "level": 2}
    if total > 10_000:
        return {"name": "🔰 Rookie", "cdMult": 1.0, "level": 1}
    return {"name": "🥚 Newbie", "cdMult": 1.0, "level": 0}

def update_street_cred(user_id: int, amount: int) -> Optional[str]:
    """Update street cred and check for achievements."""
    data = get_player_data(user_id)
    data["streetCred"] += amount
    if data["streetCred"] >= 1000 and "hood_king" not in data["achievements"]:
        data["achievements"].append("hood_king")
        data["bread"] += 500
        schedule_save()
        return "🏆 Achievement Unlocked: **Hood King**! +500 bread!"
    schedule_save()
    return None