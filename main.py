from dotenv import load_dotenv
load_dotenv()
import asyncio
import logging


from bot.config import settings
from bot.core.bot import JamalBot


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def main() -> None:
    setup_logging()

    bot = JamalBot()

    async with bot:
        await bot.start(settings.bot_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shut down.")