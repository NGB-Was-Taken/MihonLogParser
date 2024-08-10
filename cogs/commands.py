import disnake
from disnake.ext import commands
import json
from utils.paginator import ListPaginator


def get_info(bot, id):
    bot.cursor.execute("SELECT * FROM crashes WHERE id = ?", (id,))
    data = bot.cursor.fetchone()
    if data:
        return disnake.Embed(
            title=f"{data[1]} | ID: {data[0]}",
            description=f"Log string: `{data[2]}`\n\nEmbed:```json\n{json.dumps(json.loads(data[3]), indent=4)}\n```",
            color=int("02e6ff", 16),
        ).set_footer(text=f"Seen in logs {data[4]} times")
    else:
        return disnake.Embed(
            title="Error",
            description="The provided ID does not exist.",
            color=int("ff0000", 16),
        )


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
                max_length=4000,
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
        self.bot.cursor.execute("SELECT 1 FROM crashes WHERE id = ?", (self.id,))
        if self.bot.cursor.fetchone() is None:
            await inter.response.send_message("The provided ID does not exist.")
            return

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
        short_name: str,
    ):
        """
        Create a new crash entry

        Parameters
        ----------
        short_name: The short name of the crash
        """
        await inter.response.send_modal(CreateModal(self.bot, short_name))

    @crash.sub_command()
    async def edit(
        self,
        inter,
        id: int,
        short_name: str = "",
    ):
        """
        Edit an existing crash entry

        Parameters
        ----------
        id: The ID of the crash entry. (Can be found in the `crash list` command)
        short_name: The new short name of the crash
        """
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
        id: int,
    ):
        """
        Get information about a crash entry

        Parameters
        ----------
        id: The ID of the crash entry. (Can be found in the `crash list` command)
        """
        embed = get_info(self.bot, id)
        await ctx.send(embed=embed)

    @crash.sub_command(name="view")
    async def view_slash(
        self,
        inter,
        id: int,
    ):
        """
        Get information about a crash entry

        Parameters
        ----------
        id: The ID of the crash entry. (Can be found in the `crash list` command)
        """
        embed = get_info(self.bot, id)
        await inter.response.send_message(embed=embed)

    @crash_.command()
    async def delete(
        self,
        ctx,
        id: int,
    ):
        """
        Delete a crash entry

        Parameters
        ----------
        id: The ID of the crash entry. (Can be found in the `crash list` command)
        """
        self.bot.cursor.execute("DELETE FROM crashes WHERE id = ?", (id,))
        self.bot.conn.commit()
        await ctx.send(f"Deleted crash with ID {id} (even if it didn't exist)")

    @crash.sub_command(name="delete")
    async def delete_slash(
        self,
        inter,
        id: int,
    ):
        """
        Delete a crash entry

        Parameters
        ----------
        id: The ID of the crash entry. (Can be found in the `crash list` command)
        """
        self.bot.cursor.execute("DELETE FROM crashes WHERE id = ?", (id,))
        self.bot.conn.commit()
        await inter.response.send_message(
            f"Deleted crash with ID {id} (even if it didn't exist)"
        )

    @crash_.command()
    async def list(self, ctx):
        """List all the crashes in the database"""
        cursor = self.bot.cursor
        cursor.execute("SELECT id, short_name FROM crashes")
        crashes = cursor.fetchall()
        paginator = ListPaginator(
            f"Known crashes | Total: {len(crashes)}",
            [f"{_id}. {short_name}" for _id, short_name in crashes],
        )
        await ctx.send(embed=paginator.embeds[0], view=paginator)

    @crash.sub_command(name="list")
    async def list_slash(self, inter):
        """List all the crashes in the database"""
        cursor = self.bot.cursor
        cursor.execute("SELECT id, short_name FROM crashes")
        crashes = cursor.fetchall()
        paginator = ListPaginator(
            f"Known crashes | Total: {len(crashes)}",
            [f"{_id}. {short_name}" for _id, short_name in crashes],
        )
        await inter.response.send_message(embed=paginator.embeds[0], view=paginator)


def setup(bot):
    bot.add_cog(Commands(bot))
