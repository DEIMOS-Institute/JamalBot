import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
GUILD_ID = 1445307822689620090
JOSE_ID = 701435755553095761

# Roles that bypass N-word detection (boosters)
BOOSTER_ROLES = [1445970213710594260, 1460191925918367859]

# Shikyo's Services
SHIKYO_SERVICES = {
    "custom_color": {"cost": 50000, "name": "Custom Color Role", "description": "Choose your own role color"},
    "hard_r_pass": {"cost": 100000, "name": "Hard R Pass", "description": "Immunity from N-word heat"},
}

DATA_DIR = "storage"
DATA_FILE = os.path.join(DATA_DIR, "playerData.json")
AUTO_SAVE_INTERVAL = 30
INACTIVITY_THRESHOLD = 20  # minutes

# Prefix for text commands
PREFIX = "jamal" "j"