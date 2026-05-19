class PermissionManager:
    def __init__(self):
        self.auto_approve = False
        self.ask_callback = None  # The TUI will inject its modal function here!
        
    async def check_permission(self, tool_name: str, details: str) -> bool:
        """Asynchronously asks the user for permission."""
        if self.auto_approve:
            print(f"\n[⚡ Auto-approved] {tool_name}: {details}")
            return True
            
        # 1. Use the TUI Modal if it's connected
        if self.ask_callback:
            choice = await self.ask_callback(tool_name, details)
            
        # 2. Fallback to CLI if running headless
        else:
            print(f"\n[⚠️ Permission Required] The agent wants to run: {tool_name}")
            print(f"Details: {details}")
            choice = input("Allow this action? [y]es / [n]o / [a]ll in this session: ").strip().lower()
            
        # Process the choice ('yes', 'no', or 'all')
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        elif choice in ['a', 'all']:
            self.auto_approve = True
            return True
            
        return False
