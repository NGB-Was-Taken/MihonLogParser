import logging
import os
import sqlite3

import disnake
from disnake import Intents
from disnake.ext import commands

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(name)s: [%(levelname)s] - %(message)s"
)


class Bot(commands.Bot):
    def __init__(self):
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = False
        intents.typing = False

        super().__init__(
            command_prefix="&",
            intents=intents,
        )
        self.logger = logging.getLogger("Bot")
        self.token = os.getenv("BOT_TOKEN")

        self.conn = sqlite3.connect("database.db")
        self.cursor = self.conn.cursor()
        self.setup_db()

        self.load_extensions("cogs")

    def setup_db(self):
        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS version_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    major INTEGER,
                    minor INTEGER,
                    patch INTEGER
                )
            """
        )

        self.cursor.execute(
            """
                SELECT 1 FROM version_info
            """
        )

        if self.cursor.fetchone() is None:
            self.cursor.execute(
                """
                    INSERT INTO version_info (major, minor, patch)
                    VALUES (0, 0, 0)
                """
            )

        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS crashes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    short_name TEXT,
                    message TEXT,
                    response TEXT,
                    times_used INTEGER
                )
            """
        )
        self.conn.commit()

    def run(self):
        super().run(self.token)

    async def close(self):
        await super().close()
        self.conn.close()


bot = Bot()


@bot.check
async def check(ctx: commands.Context):

    roles_to_check = {
        123,
        456,
        789,
    }
    if not ctx.guild:
        raise commands.NoPrivateMessage
    if roles_to_check & {role.id for role in ctx.author.roles}:
        return True
    raise commands.MissingRole("Error")


@bot.slash_command_check
async def check_slash(inter: disnake.AppCommandInteraction):
    roles_to_check = {
        123,
        456,
        789,
    }
    if not inter.guild:
        raise commands.NoPrivateMessage
    if roles_to_check & {role.id for role in inter.author.roles}:
        return True
    raise commands.MissingRole


bot.run()
