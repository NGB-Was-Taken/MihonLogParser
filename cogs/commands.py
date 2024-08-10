import disnake
from disnake.ext import commands
import json


class CrashModal(disnake.ui.Modal):
    def __init__(self, bot, short_name):
        self.bot = bot
        self.short_name = short_name
        components = [
            disnake.ui.TextInput(
                label="Crash Message",
                placeholder="Message to look for in the crash log.",
                custom_id="message",
                style=disnake.TextInputStyle.long,
                max_length=2048,
                required=True,
            ),
            disnake.ui.TextInput(
                label="Title",
                placeholder="Title of the embed",
                custom_id="title",
                style=disnake.TextInputStyle.short,
                max_length=256,
                required=True,
            ),
            disnake.ui.TextInput(
                label="Description",
                placeholder="Description of the embed",
                custom_id="description",
                style=disnake.TextInputStyle.paragraph,
                max_length=3000,
                required=True,
            ),
            disnake.ui.TextInput(
                label="Image URL",
                placeholder="Image URL of the embed",
                custom_id="image",
                style=disnake.TextInputStyle.short,
                max_length=256,
                required=False,
            ),
            disnake.ui.TextInput(
                label="Color",
                placeholder="Color of the embed in hex. (Defaults to black)",
                custom_id="color",
                style=disnake.TextInputStyle.short,
                min_length=6,
                max_length=6,
                required=False,
            ),
        ]
        super().__init__(title="Add a crash.", custom_id="crash", components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        if inter.text_values["image"] and not inter.text_values["image"].startswith(
            "http"
        ):
            await inter.response.send_message("Image URL must start with http")
            return
        try:
            self.embed_dict = {
                "title": inter.text_values["title"],
                "description": inter.text_values["description"],
                "image": (
                    {"url": inter.text_values["image"]}
                    if inter.text_values["image"]
                    else None
                ),
                "color": (
                    int(inter.text_values["color"], 16)
                    if inter.text_values["color"]
                    else 0
                ),
            }
        except ValueError:
            await inter.response.send_message(
                "Invalid color value. Valid characters are [0-9a-fA-F]"
            )
            return
        return True

    async def on_error(self, error, inter) -> None:
        self.bot.logger.error(error)
        await inter.response.send_message(f"An error has occured and has been logged.")


class CreateModal(CrashModal):
    async def callback(self, inter: disnake.ModalInteraction) -> None:
        if not await super().callback(inter):
            return
        if self.embed_dict:
            self.bot.cursor.execute(
                """
                                    INSERT INTO crashes
                                    (short_name, message, response, times_used)
                                    VALUES
                                    (?, ?, ?, 0)
                                    """,
                (
                    self.short_name,
                    inter.text_values["message"],
                    json.dumps(self.embed_dict),
                ),
            )
            self.bot.conn.commit()
            await inter.response.send_message(
                "Added the crash to the database.",
                embed=disnake.Embed.from_dict(self.embed_dict),
            )


class EditModal(CrashModal):
    def __init__(self, bot, short_name, id: int):
        super().__init__(bot, short_name)
        self.id = id

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        if not await super().callback(inter):
            return
        if self.embed_dict:
            self.bot.cursor.execute(
                f"""
                                    UPDATE crashes
                                    {f'SET short_name = {
                self.short_name}' if self.short_name else ''}
                                    SET message = ?
                                    SET response = ?
                                    WHERE id = ?
                                    """,
                (inter.text_values["message"], json.dumps(self.embed_dict), self.id),
            )
            self.bot.conn.commit()
            await inter.response.send_message(
                "Edited the crash in the database.",
                embed=disnake.Embed.from_dict(self.embed_dict),
            )


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cursor = bot.cursor
        self.conn = bot.conn

    @commands.command()
    async def update(self, ctx, major: int, minor: int, patch: int):
        """Change the latest Mihon version"""
        self.cursor.execute(
            """
                            UPDATE version_info
                            SET major = ?,
                                minor = ?,
                                patch = ?
                            WHERE id = 1
                            """,
            (major, minor, patch),
        )
        self.conn.commit()
        self.bot.get_cog("Events").fetch_version()
        await ctx.send("Updated version to {}.{}.{}".format(major, minor, patch))

    @commands.slash_command()
    async def crash(self, inter):
        """Commands for managing crash entries and responses."""
        pass

    @crash.sub_command()
    async def create(
        self,
        inter,
        short_name: str = disnake.Option(
            name="short_name", description="The short name of the crash", required=True
        ),
    ):
        """Create a new crash entry"""
        await inter.response.send_modal(CreateModal(self.bot, short_name))

    @crash.sub_command()
    async def edit(
        self,
        inter,
        id: int = disnake.Option(
            name="id",
            description="The ID of the crash entry. (Can be found in the `crash list` command)",
        ),
        short_name: str = disnake.Option(
            name="short_name", description="New short name of the crash", required=False
        ),
    ):
        """Edit an existing crash entry"""
        await inter.response.send_modal(EditModal(self.bot, short_name, id))

    @commands.group(name="crash")
    async def crash_(self, ctx):
        """Commands for managing crash entries and responses."""
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Run the command with either `view <id>`, `delete <id>` or `list`"
            )

    @crash_.command()
    async def view(
        self,
        ctx,
        id: int = disnake.Option(
            name="id",
            description="The ID of the crash entry. (Can be found in the `crash list` command)",
        ),
    ):
        pass

    @crash_.command()
    async def delete(
        self,
        ctx,
        id: int = disnake.Option(
            name="id",
            description="The ID of the crash entry. (Can be found in the `crash list` command)",
        ),
    ):
        pass

    @crash_.command()
    async def list(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Commands(bot))
