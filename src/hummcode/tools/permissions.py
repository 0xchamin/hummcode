class PermissionManager:
    def __init__(self):
        # Starts false so we always ask for the first dangerous action
        self.auto_approve = False
        
    def check_permission(self, tool_name: str, details: str) -> bool:
        """Asks the user for permission to run a dangerous tool."""
        
        # If the user previously selected "yes to all", skip the prompt
        if self.auto_approve:
            print(f"\n[⚡ Auto-approved] {tool_name}: {details}")
            return True
            
        print(f"\n[⚠️ Permission Required] The agent wants to run: {tool_name}")
        print(f"Details: {details}")
        
        while True:
            choice = input("Allow this action? [y]es / [n]o / [a]ll in this session: ").strip().lower()
            
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            elif choice in ['a', 'all']:
                self.auto_approve = True
                print("[🔒 Auto-approve enabled for the rest of this session]")
                return True
            else:
                print("Invalid choice. Please type 'y', 'n', or 'a'.")
