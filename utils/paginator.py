import disnake


class ListPaginator(disnake.ui.View):
    def __init__(self, embed_title, embed_description):
        super().__init__(
            timeout=None,
        )
        self.embed_title = embed_title
        self.embed_description = embed_description
        self.embeds = []
        self.index = 0
        self.build_embeds()
        self._update_state()

    def _update_state(self):
        self.prev_page.disabled = self.index == 0
        self.next_page.disabled = self.index == len(self.embeds) - 1

    def build_embeds(self):
        pages = []
        for i in range(0, len(self.embed_description), 15):
            pages.append("\n".join(self.embed_description[i : i + 15]))

        for i, page in enumerate(pages):
            embed = disnake.Embed(
                title=self.embed_title,
                description=page,
            )
            embed.set_footer(text=f"Page {i + 1} of {len(pages)}")
            self.embeds.append(embed)

    @disnake.ui.button(label="<", style=disnake.ButtonStyle.gray)
    async def prev_page(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        self.index -= 1

        await inter.response.edit_message(embed=self.embeds[self.index], view=self)

    @disnake.ui.button(label="X", style=disnake.ButtonStyle.red)
    async def remove(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        await inter.response.edit_message(view=None)

    @disnake.ui.button(label=">", style=disnake.ButtonStyle.gray)
    async def next_page(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        self.index += 1

        await inter.response.edit_message(embed=self.embeds[self.index], view=self)
