    # def highlight_current_desktop(self):
    #     if self.shift_pressed:
    #         return

    #     active_desktop = VirtualDesktop.current()
    #     active_desktop_index = active_desktop.number
    #     for index, button in enumerate(self.buttons, start=1):
    #         if str(index) == str(active_desktop_index):
    #             # button.config(bg="")
    #         else:
    #             button.config(bg="#1e2127")
    #     self.after(420, self.highlight_current_desktop)