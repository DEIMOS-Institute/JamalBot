import json
import asyncio
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from .models import DEFAULT_PLAYER_DATA
from ..config import DATA_FILE, DATA_DIR

player_data: Dict[int, Dict] = {}
save_timeout: Optional[asyncio.Task] = None
backup_timeout: Optional[asyncio.Task] = None
BACKUP_DIR = os.path.join(DATA_DIR, "backups")


def load_player_data():
    """Load player data from JSON file."""
    global player_data
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        player_data = {}
        for entry in data:
            user_id = int(entry[0])
            user_data = entry[1]
            merged = DEFAULT_PLAYER_DATA.copy()
            merged.update(user_data)
            if "hood" in user_data:
                merged["hood"] = {**DEFAULT_PLAYER_DATA["hood"], **user_data["hood"]}
            else:
                merged["hood"] = DEFAULT_PLAYER_DATA["hood"].copy()
            player_data[user_id] = merged
        print(f"✅ Loaded {len(player_data)} player records")
    except FileNotFoundError:
        print("📁 No existing player data found, starting fresh")
        player_data = {}
    except Exception as e:
        print(f"❌ Error loading player data: {e}")
        player_data = {}


def save_player_data_sync():
    """Save player data to JSON file synchronously."""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        data_array = [[str(uid), data] for uid, data in player_data.items()]
        temp_file = Path(DATA_FILE).with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data_array, f, indent=2)
        temp_file.replace(DATA_FILE)
        print(f"💾 Saved {len(player_data)} player records")
    except Exception as e:
        print(f"❌ Error saving player data: {e}")


async def save_player_data(immediate: bool = False):
    """Save player data asynchronously with optional immediate save."""
    global save_timeout
    if save_timeout and not immediate:
        save_timeout.cancel()
        save_timeout = None

    async def save_func():
        await asyncio.to_thread(save_player_data_sync)

    if immediate:
        await save_func()
    else:
        async def delayed_save():
            await asyncio.sleep(5)
            await save_func()
        save_timeout = asyncio.create_task(delayed_save())


def schedule_save():
    """Schedule a delayed save."""
    asyncio.create_task(save_player_data(False))


def create_backup():
    """Create a backup of player data with timestamp."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"playerData_backup_{timestamp}.json")
        data_array = [[str(uid), data] for uid, data in player_data.items()]
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data_array, f, indent=2)
        print(f"💾 Backup created: {backup_file}")
        
        # Keep only the last 100 backups to save space
        cleanup_old_backups(max_backups=100)
    except Exception as e:
        print(f"❌ Error creating backup: {e}")


def cleanup_old_backups(max_backups: int = 100):
    """Remove old backups, keeping only the most recent ones."""
    try:
        if not os.path.exists(BACKUP_DIR):
            return
        
        backup_files = sorted([
            os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR)
            if f.startswith("playerData_backup_") and f.endswith(".json")
        ], key=os.path.getctime)
        
        if len(backup_files) > max_backups:
            for old_file in backup_files[:-max_backups]:
                os.remove(old_file)
                print(f"🗑️ Deleted old backup: {old_file}")
    except Exception as e:
        print(f"⚠️ Error cleaning up backups: {e}")


async def backup_loop():
    """Continuously create backups every 15 seconds."""
    global backup_timeout
    while True:
        try:
            await asyncio.sleep(15)
            await asyncio.to_thread(create_backup)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ Error in backup loop: {e}")


def start_backup_loop():
    """Start the automatic backup loop."""
    global backup_timeout
    backup_timeout = asyncio.create_task(backup_loop())
    print("🔄 Backup loop started (15 second intervals)")


async def stop_backup_loop():
    """Stop the backup loop."""
    global backup_timeout
    if backup_timeout:
        backup_timeout.cancel()
        try:
            await backup_timeout
        except asyncio.CancelledError:
            pass
        print("⏹️ Backup loop stopped")


def get_player_data(user_id: int) -> dict:
    """Get or create player data for a user."""
    if user_id not in player_data:
        data = DEFAULT_PLAYER_DATA.copy()
        data["hood"] = DEFAULT_PLAYER_DATA["hood"].copy()
        player_data[user_id] = data
        schedule_save()
    return player_data[user_id]


def calculate_earnings(base_amount: int, user_id: int) -> int:
    """Calculate earnings with all multipliers and effects applied."""
    data = get_player_data(user_id)
    current_time = int(time.time())

    # Base multiplier
    total_multiplier = data["multiplier"]

    # Cred multiplier from prestige items
    total_multiplier *= data.get("cred_multiplier", 1.0)

    # Active boosts
    active_boosts = data.get("active_boosts", {})
    if "earnings" in active_boosts:
        boost = active_boosts["earnings"]
        if current_time < boost.get("expires", 0):
            total_multiplier *= boost.get("multiplier", 1.0)
        else:
            # Boost expired, remove it
            del active_boosts["earnings"]
            schedule_save()

    # Active debuffs
    active_debuffs = data.get("active_debuffs", {})
    if "intimidated" in active_debuffs:
        debuff = active_debuffs["intimidated"]
        if current_time < debuff.get("expires", 0):
            total_multiplier *= debuff.get("earnings_penalty", 1.0)
        else:
            # Debuff expired, remove it
            del active_debuffs["intimidated"]
            schedule_save()

    return int(base_amount * total_multiplier)