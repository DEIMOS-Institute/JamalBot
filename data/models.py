from typing import Dict, Any

DEFAULT_PLAYER_DATA: Dict[str, Any] = {
    # Core economy
    "bread": 1000,
    "streetCred": 0,
    "multiplier": 1.0,
    "heat": 0,
    "respect": 50,

    # Inventory & Storage
    "inventory": [],
    "stashedBread": 0,
    "stashCapacity": 5000,
    "safeBalance": 0,
    "safeCapacity": 10000,

    # New: Collectibles
    "collectibles": [],  # List of dicts: {"id": "golden_chain", "rarity": "legendary"}

    # New: Investments
    "investments": {},  # Dict: {"trap_house": {"level": 1, "last_collect": 0, "yield": 100}}

    # New: Black Market
    "black_market_items": [],  # List of illegal items for trade

    # New: Storytelling Progress
    "story_progress": {},  # Dict for branching narratives, e.g., {"loyalty_path": "snitch"}

    # Cooldowns
    "lastDaily": 0,
    "lastWeekly": 0,
    "lastMonthly": 0,
    "lastWork": 0,
    "lastRob": 0,
    "lastLick": 0,
    "lastScavenge": 0,
    "lastHustle": 0,
    "lastCrime": 0,
    "lastGamble": 0,
    "lastSlots": 0,
    "lastRace": 0,
    "lastDrill": 0,
    "lastTrap": 0,
    "lastStickup": 0,
    "lastInterest": 0,

    # Streaks
    "streak": {
        "daily": 0,
        "weekly": 0,
        "monthly": 0,
    },

    # Stats
    "roastsGiven": 0,
    "roastsReceived": 0,
    "casesWon": 0,
    "casesLost": 0,
    "drillsCompleted": 0,
    "smokeCount": 0,
    "bitches": 0,
    "rep": 0,

    # Achievements & Badges
    "achievements": [],
    "badges": [],

    # Hood System
    "hood": {
        "name": None,
        "joined": 0,
        "loyalty": 0,
        "lastLoyaltyUpdate": 0,
    },
    "turf": None,
    "turfIncome": 0,
    "lastTurfCollect": 0,

    # Crew/Gang
    "crew": None,
    "crewRole": None,

    # Social
    "beefs": [],
    "dripLevel": 1,
    "nickname": None,

    # Drugs
    "drugs": {
        "weed": 0,
        "coke": 0,
        "pills": 0,
    },
    "growOp": {
        "plants": 0,
        "plantedAt": 0,
    },

    # Loan
    "loanAmount": 0,
    "loanDue": 0,

    # Investments
    "investments": {},

    # Shikyo Services
    "purchased_services": [],

    # Trap House
    "trapHouseLevel": 1,

    # Bounty System
    "bounties_set": [],  # List of bounties this player has placed
    "active_hits": [],   # List of bounty IDs this player has claimed

    # Street Cred Multipliers
    "cred_multiplier": 1.0,  # Multiplier from prestige items
    "vip_pass": False,       # VIP hood pass access

    # Active Effects
    "active_boosts": {},     # Temporary boosts from street cred spending
    "active_debuffs": {},    # Temporary debuffs from intimidation etc
}