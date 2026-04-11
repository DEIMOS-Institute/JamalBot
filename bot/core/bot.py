import logging

import discord
from discord.ext import commands

from bot.config import settings

log = logging.getLogger(__name__)


class JamalBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(
                settings.prefix_one,
                settings.prefix_two,
            ),
            intents=intents,
            help_command=None,
        )

        self.initial_extensions = [
            "bot.cogs.utility",
        ]

    async def setup_hook(self) -> None:
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                log.info("Loaded extension: %s", extension)
            except Exception:
                log.exception("Failed to load extension: %s", extension)

        # Faster slash command syncing for development if you set a guild ID.
        if settings.sync_guild_id:
            guild = discord.Object(id=settings.sync_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %s guild app commands.", len(synced))
        else:
            synced = await self.tree.sync()
            log.info("Synced %s global app commands.", len(synced))

    async def on_ready(self) -> None:
        if self.user is not None:
            log.info("Logged in as %s (%s)", self.user, self.user.id)