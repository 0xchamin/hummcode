from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Label
from textual.suggester import SuggestFromList
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.containers import Vertical, Horizontal, Container

from hummcode.core import HummcodeAgent

class PermissionModal(ModalScreen[str]):
    """A modal to ask for permission before running dangerous tools."""
    
    def __init__(self, tool_name: str, details: str):
        super().__init__()
        self.tool_name = tool_name
        self.details = details

    def compose(self) -> ComposeResult:
        with Vertical(id="permission-dialog"):
            yield Label(f"[b][#fbbf24]⚠️ Permission Required[/#fbbf24][/b]\nThe agent wants to run: [b]{self.tool_name}[/b]")
            yield Label(f"Details: {self.details}\n")
            with Horizontal(id="permission-buttons"):
                yield Button("Yes", variant="success", id="yes")
                yield Button("No", variant="error", id="no")
                yield Button("Yes to All", variant="primary", id="all")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # This sends the button's ID ('yes', 'no', or 'all') back to whatever called the modal
        self.dismiss(event.button.id)


class HummcodeApp(App):
    """The Hummcode Terminal UI."""
    CSS_PATH = "themes/default.tcss"
    

    def __init__(self):
        super().__init__()
        self.agent = HummcodeAgent()

    def compose(self) -> ComposeResult:
        """Construct the UI layout."""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            yield RichLog(id="chat-log", markup=True, wrap=True)
            yield RichLog(id="tool-log", markup=True, wrap=True)
            
            # The list of commands we want to auto-suggest
            COMMANDS = ["/info", "/list", "/model ", "/clear", "/rewind", "/key "]
            
            yield Input(
                placeholder="Type a message, or type / for commands...", 
                id="chat-input",
                suggester=SuggestFromList(COMMANDS, case_sensitive=False)
            )
        yield Label(" Commands: /info | /list | /model | /key | /clear | /rewind", id="cheat-sheet")  


    def on_mount(self) -> None:
        self.title = "Hummcode"
        self.sub_title = f"Active Model: {self.agent.llm.default_model}"
        # Inject our TUI callback into the agent's brain
        self.agent.perm_manager.ask_callback = self.ask_permission
        
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write("[b][#a7f3d0]🐦 Welcome to Hummcode![/#a7f3d0][/b]")
        chat_log.write("The Hummingbird Agentic Coding Agent built from first principles.\n")

    async def ask_permission(self, tool_name: str, details: str) -> str:
        """Pops up the modal and waits for the user's choice."""
        # This pushes the modal to the screen and 'awaits' the user's click!
        choice = await self.push_screen_wait(PermissionModal(tool_name, details))
        return choice

    
    @work
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handles the user pressing Enter in the input box."""
        user_text = event.value.strip()

        #to cleanly exit
        if user_text.lower() in ['exit', 'quit', ':q']:
            self.exit()
            return
        
        if not user_text:
            return

        # 1. Clear input and grab our log panes
        event.input.value = ""
        chat_log = self.query_one("#chat-log", RichLog)
        tool_log = self.query_one("#tool-log", RichLog)
        
        # 2. Write the user's message to the main chat
        chat_log.write(f"\n[b][#38bdf8]You:[/#38bdf8][/b] {user_text}")

        # 3. Stream the async events from our core brain!
        async for update in self.agent.process_prompt(user_text):
            event_type = update.get("type")
            content = update.get("content", "")

            # Route the events to the correct pane based on their type
            if event_type == "system":
                chat_log.write(f"[b][#fbbf24]System:[/#fbbf24][/b] {content}")
            elif event_type == "status":
                tool_log.write(f"[#94a3b8]{content}[/#94a3b8]")
            elif event_type == "tool_result":
                tool_log.write(f"[#475569]{content}[/#475569]\n")
            elif event_type == "message":
                chat_log.write(f"\n[b][#a7f3d0]Hummcode:[/#a7f3d0][/b]\n{content}\n")

    def action_change_model(self) -> None:
        self.notify("The Model Pop-up Modal is coming next!")

    def action_settings(self) -> None:
        self.notify("The Settings Modal is coming next!")

if __name__ == "__main__":
    app = HummcodeApp()
    app.run()
