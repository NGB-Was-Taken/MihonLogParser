from disnake.ext import commands
import disnake
import re
import json


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.version_pattern = re.compile(r"(\d+)\.(\d+)\.(\d+)")
        self.log_pattern = re.compile(
            r"\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} +\d+ +\d+ [A-Z] (.*)"
        )
        self.fetch_version()

    def fetch_version(self):
        self.bot.cursor.execute(
            """
                                SELECT major, minor, patch
                                FROM version_info
                                """
        )
        self.versions = self.bot.cursor.fetchone()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Bot is ready.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(error)
        elif isinstance(error, commands.MissingRole):
            await ctx.message.add_reaction("\N{WARNING SIGN}")
        else:
            await ctx.send("An error occured and has been logged.")
            self.bot.logger.error(error, exc_info=error)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        for attachment in message.attachments:
            if (
                attachment.content_type == "text/plain; charset=utf-8"
                and attachment.filename.endswith(".txt")
            ):
                file = (await attachment.read()).decode().splitlines()

                majorVer, minorVer, patchVer = self.version_pattern.search(
                    file[0]
                ).groups()
                if (
                    self.versions[0] > int(majorVer)
                    or self.versions[1] > int(minorVer)
                    or self.versions[2] > int(patchVer)
                ):
                    await message.reply(
                        "Looks like you aren't on the latest version. Please update your app and see if fixes your issue"
                    )
                log_message = []
                for line in file:
                    match = self.log_pattern.match(line)
                    if match:
                        log_message.append(match.group(1))
                if log_message:
                    self.bot.cursor.execute(
                        f"""
                                            SELECT id, response FROM crashes
                                            WHERE message IN ({','.join(['?']*len(log_message))})
                                            LIMIT 1
                                            """,
                        log_message,
                    )
                    response = self.bot.cursor.fetchone()
                    if response:
                        self.bot.cursor.execute(
                            f"""
                                                UPDATE crashes
                                                SET times_used = times_used + 1
                                                WHERE id = {response[0]}
                                                """
                        )
                        self.bot.conn.commit()
                        await message.reply(
                            embed=disnake.Embed.from_dict(json.loads(response[1]))
                        )
                elif [
                    atch
                    for atch in message.attachments
                    if atch.content_type.startswith("image/")
                ]:
                    pass
                else:
                    await message.reply(
                        "Your log file doesn't contain any useful logs. Please send a screenshot of the crash screen if possible."
                    )


def setup(bot):
    bot.add_cog(Events(bot))
