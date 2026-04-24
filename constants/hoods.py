HOODS = {
    "southside": {
        "name": "Southside",
        "fullName": "🏚️ Southside – The Bottom",
        "story": "Southside is where the city was born – old brick buildings, corner stores, and generations of families. It's poor but proud. Everybody knows everybody, and loyalty runs deep. The cops don't come around much, so the streets run on their own code. If you're from The Bottom, you learn to survive with what you got.",
        "perks": {
            "description": "• **Hood Famous** – +10% respect gain (lower heat from small crimes)\n• **Hand Me Downs** – 5% chance to find an extra item when scavenging\n• **Family Ties** – Slightly better prices from Jamal",
            "modifiers": {
                "heatFromSmallCrimes": 0.9,
                "scavengeBonusChance": 0.05,
                "shopDiscount": 0.95,
            }
        },
        "color": 0x8B4513,
        "emoji": "🏚️"
    },
    "northside": {
        "name": "Northside",
        "fullName": "🏙️ Northside – Uptown",
        "story": "Uptown is where dreams are made – high-rises, fancy boutiques, and celebrities. Everyone here is trying to make it big. The hustle is real, but so are the eyes. Cops patrol regularly, so you gotta be slick. Uptown is for those who want the spotlight but can handle the heat.",
        "perks": {
            "description": "• **Glossy Drip** – +15% earnings from legal work\n• **Connections** – Better odds in gambling (win chance +5%)\n• **Safe Streets** – Stash house has +20% default security",
            "modifiers": {
                "workEarnings": 1.15,
                "gambleWinChance": 0.05,
                "stashSecurity": 1.2,
            }
        },
        "color": 0x1E90FF,
        "emoji": "🏙️"
    },
    "eastside": {
        "name": "Eastside",
        "fullName": "🏭 Eastside – The Industrial",
        "story": "Factories, warehouses, and abandoned lots – Eastside is the city's engine room. It's rough, loud, and full of opportunities if you're willing to get your hands dirty. The real money is in moving product through the industrial corridors. You'll work hard, but you'll eat well.",
        "perks": {
            "description": "• **Heavy Lifting** – +20% earnings from `/hustle work`\n• **Warehouse Access** – +10% stash capacity\n• **No Questions Asked** – 10% cheaper black market prices",
            "modifiers": {
                "hustleWorkEarnings": 1.2,
                "stashCapacity": 1.1,
                "blackMarketDiscount": 0.9,
            }
        },
        "color": 0x808080,
        "emoji": "🏭"
    },
    "westside": {
        "name": "Westside",
        "fullName": "🏡 Westside – The Suburbs",
        "story": "The suburbs look peaceful – manicured lawns, white picket fences. But underneath, it's where white-collar crime thrives. Identity theft, credit card fraud, and quiet deals in home offices. Westsiders are sneaky; they don't look like criminals, but they run the digital streets.",
        "perks": {
            "description": "• **Clean Cut** – Heat decays 20% faster\n• **Digital Hustle** – Better outcomes from `/crime` (tech crimes)\n• **Garage Stash** – Car items are 15% more effective",
            "modifiers": {
                "heatDecay": 1.2,
                "crimeSuccessTech": 1.15,
                "carEffectiveness": 1.15,
            }
        },
        "color": 0x32CD32,
        "emoji": "🏡"
    },
    "downtown": {
        "name": "Downtown",
        "fullName": "🏢 Downtown – The Core",
        "story": "Downtown is the heart of power – city hall, corporate towers, and underground clubs. It's where deals are made and backs are stabbed. You're either a player or a pawn. Downtown demands respect, connections, and a thick skin. If you can make it here, you can make it anywhere.",
        "perks": {
            "description": "• **City Hall Connections** – 20% lower fines\n• **Elite Network** – Access to high-stakes gambling (higher limits, +10% odds)\n• **Insider Trading** – +5% on investments",
            "modifiers": {
                "fineReduction": 0.8,
                "gambleHighStakes": True,
                "investmentBonus": 1.05,
            }
        },
        "color": 0x800080,
        "emoji": "🏢"
    }
}