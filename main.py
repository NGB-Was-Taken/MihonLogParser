from disnake.ext import commands
from disnake import Intents
from utils.logger import Logger
import os
import sqlite3


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="&",
            intents=Intents(messages=True, message_content=True),
            reload=True,
        )
        self.logger = Logger("bot")
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
bot.run()
