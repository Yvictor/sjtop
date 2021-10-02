from textual.app import App

class SJTop(App):

    async def on_load(self) -> None:
        """Sent before going in to application mode."""

        # Bind our basic keys
        # await self.bind("b", "view.toggle('sidebar')", "Toggle sidebar")
        await self.bind("q", "quit", "Quit")

    async def on_mount(self) -> None:
        """Call after terminal goes in to application mode"""
        pass
