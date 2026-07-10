

import tkinter as tk

class VirtualKeyboard(tk.Toplevel):
    def __init__(self, entry):
        tk.Toplevel.__init__(self)
        self.entry = entry
        self.title("Virtual Keyboard")
        self.attributes('-toolwindow', True)  # Remove minimize, maximize, and close buttons
        self.lowercase = False
        self.buttons = [
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'BS'
            'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Space', 'Enter', 'Shift'
        ]
        self.draw_keyboard()

    def draw_keyboard(self):
        row = 1
        col = 0
        for button in self.buttons:
            command = lambda x=button: self.click(x)
            if button in ["Space", "Backspace", "Enter", "Shift"]:
                tk.Button(self, text=button, width=10, command=command).grid(row=row, column=col, columnspan=5)
                col += 10
            else:
                tk.Button(self, text=button, width=5, command=command).grid(row=row, column=col)
                col += 1
            if col > 9:
                col = 0
                row += 1

    def click(self, value):
        if value == "Backspace":
            self.entry.delete(len(self.entry.get())-1, 'end')
        elif value == "Space":
            self.entry.insert('end', ' ')
        elif value == "Enter":
            self.destroy()  # Close the virtual keyboard
        elif value == "Shift":
            self.lowercase = not self.lowercase  # Toggle between lowercase and uppercase
            for button in self.buttons:
                if button not in ["Space", "Backspace", "Enter", "Shift"]:
                    if self.lowercase:
                        button = button.lower() 
                    else:
                        button = button.upper() 
                  
        else:
            self.entry.insert('end', value.lower() if self.lowercase else value.upper())

