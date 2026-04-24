import discord
from ..constants.items import SHOP_ITEMS, SHIKYO_SERVICES
from ..data import get_player_data, schedule_save

class ShopView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.add_item(ShopCategorySelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

class ShopCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Multipliers", value="multiplier", emoji="📈"),
            discord.SelectOption(label="Equipment", value="equipment", emoji="🔫"),
            discord.SelectOption(label="Drip", value="drip", emoji="💎"),
            discord.SelectOption(label="Drugs", value="drug", emoji="💊"),
            discord.SelectOption(label="Prestige Items", value="prestige", emoji="🏆"),
            discord.SelectOption(label="Shikyo Services", value="shikyo", emoji="👑"),
        ]
        super().__init__(placeholder="Select a category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        category = self.values[0]
        if category == "shikyo":
            embed = discord.Embed(title="👑 Shikyo's Premium Services", color=0xffd700)
            for key, service in SHIKYO_SERVICES.items():
                embed.add_field(
                    name=f"{service['name']} - {service['cost']} bread",
                    value=service['description'],
                    inline=False
                )
            view = ShikyoPurchaseView(interaction.user.id)
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            items = {k: v for k, v in SHOP_ITEMS.items() if v.get("type") == category}
            embed = discord.Embed(title=f"🛒 {category.title()} Shop", color=0x00ff00)
            for key, item in items.items():
                req_text = ""
                if "street_cred_req" in item:
                    req_text = f" (Requires {item['street_cred_req']} ⭐)"
                embed.add_field(
                    name=f"{item['name']} - {item['cost']} bread{req_text}",
                    value=f"Use `/buy {key}` to purchase",
                    inline=True
                )
            await interaction.edit_original_response(embed=embed, view=None)

class ShikyoPurchaseView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        for key, service in SHIKYO_SERVICES.items():
            self.add_item(ShikyoBuyButton(key, service))

class ShikyoBuyButton(discord.ui.Button):
    def __init__(self, service_id: str, service: dict):
        super().__init__(
            label=f"Buy {service['name']} - {service['cost']} bread",
            style=discord.ButtonStyle.success,
            custom_id=f"buy_shikyo_{service_id}"
        )
        self.service_id = service_id
        self.service = service

    async def callback(self, interaction: discord.Interaction):
        data = get_player_data(interaction.user.id)
        if self.service_id in data.get("purchased_services", []):
            await interaction.response.send_message("You already own this service!", ephemeral=True)
            return
        if data["bread"] < self.service["cost"]:
            await interaction.response.send_message(f"You need {self.service['cost']} bread!", ephemeral=True)
            return
        data["bread"] -= self.service["cost"]
        data["purchased_services"].append(self.service_id)
        schedule_save()
        await interaction.response.send_message(f"✅ You purchased **{self.service['name']}**! Staff will apply it soon.", ephemeral=True)