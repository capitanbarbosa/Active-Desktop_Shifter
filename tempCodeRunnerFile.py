    def shortcut3(self, index):
        if index < 1 or index > 7:
            print("Invalid index number. Please provide a number between 1 and 7.")
            return
        
        script_path = os.path.join("DesktopSwitcher", f"DesktopSwitcher-d{index}.ahk")
        script_path = os.path.abspath(script_path)
        
        try:
            subprocess.run(["autohotkey", script_path], check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to execute the AHK script: {script_path}")
