import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class ClientGUI(tk.Tk):
    def __init__(self, module, client):
        super().__init__()

        self.title("Client GUI")
        self.geometry("490x350")

        self.module = module
        self.client = client

        self.state = None

        self.create_login_widgets()

        # Bind the closing event to the on_close method
        self.protocol("WM_DELETE_WINDOW", self.on_close)


    def create_login_widgets(self):
        self.user_label = ttk.Label(self, text="Username:")
        self.user_label.grid(row=0, column=0, pady=10)
        self.user_entry = ttk.Entry(self)
        self.user_entry.grid(row=0, column=1, pady=10)
        self.user_entry.focus_set()

        self.password_label = ttk.Label(self, text="Password:")
        self.password_label.grid(row=1, column=0, pady=10)
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.grid(row=1, column=1, pady=10)

        self.login_button = ttk.Button(self, text="Login", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=10)
        self.state = "login"

        self.signup_button = ttk.Button(self, text="Create Account Instead", command=self.show_signup_gui)
        self.signup_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.bind("<Return>", lambda event: self.login())
    
    def create_signup_widgets(self):
        self.user_label = ttk.Label(self, text="Username:")
        self.user_label.grid(row=0, column=0, pady=10)
        self.user_entry = ttk.Entry(self)
        self.user_entry.grid(row=0, column=1, pady=10)
        self.user_entry.focus_set()

        self.password_label = ttk.Label(self, text="Password:")
        self.password_label.grid(row=1, column=0, pady=10)
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.grid(row=1, column=1, pady=10)

        self.confirm_password_label = ttk.Label(self, text="Confirm Password:")
        self.confirm_password_label.grid(row=2, column=0, pady=10)
        self.confirm_password_entry = ttk.Entry(self, show="*")
        self.confirm_password_entry.grid(row=2, column=1, pady=10)

        self.signup_button = ttk.Button(self, text="Create Account", command=self.create_user)
        self.signup_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.login_button = ttk.Button(self, text="Login Instead", command=self.show_login_gui)
        self.login_button.grid(row=4, column=1, columnspan=2, pady=10)

        self.bind("<Return>", lambda event: self.create_user())

    def create_command_widgets(self):
        self.output_text = tk.Text(self, wrap="word", height=15, width=50)
        self.output_text.grid(row=0, column=0, pady=10, columnspan=2)

        self.input_entry = ttk.Entry(self, width=30)
        self.input_entry.grid(row=1, column=0, pady=10)
        self.input_entry.focus_set()

        self.send_button = ttk.Button(self, text="Send", command=self.send_command)
        self.send_button.grid(row=1, column=1, pady=10)

        if self.module.authentication_level == "admin":
            self.admin_button = ttk.Button(self, text="Admin", command=self.show_admin_gui)
            self.admin_button.grid(row=1, column=2, pady=10)
        
        self.state = "command"
        # print(self.state)

        self.bind("<Return>", lambda event: self.send_command())
    
    def create_admin_widgets(self):
        self.tree = ttk.Treeview(self, columns=('User', 'Privilege'), show='headings')
        self.tree.heading('User', text='User')
        self.tree.heading('Privilege', text='Privilege')
        self.tree.grid(row=0, column=0, pady=10, columnspan=3)

        # Button to change privilege level
        self.change_privilege_btn = ttk.Button(self, text='Change Privilege', command=self.change_privilege)
        self.change_privilege_btn.grid(row=1, column=0, pady=10)
        self.back_btn = ttk.Button(self, text='back', command=self.show_command_gui)
        self.back_btn.grid(row=1, column=1, pady=10)

        self.state = "admin"
        # print(self.state)


    def show_admin_gui(self):
        if self.module.state != "download":

            self.destroy_widgets()
            self.create_admin_widgets()
            self.module.create_message("userdata")
        else:
            self.show_popup_message("Wait for download to finish.")
    
    def list_all_user_privileges(self, response):
        try:
            users = response.split("\n")
            for item in users:
                user, privilege = item.split(" ")
                self.tree.insert('', 'end', values=(user, privilege))
        except:
            pass

    def change_privilege(self):
        selected_item = self.tree.selection()  # Get the selected item
        if selected_item:  # Check if any item is selected
            item_value = self.tree.item(selected_item, "values")  # Retrieve the text of the selected item
            self.module.create_message(f"privilege {item_value[0]}")
            # clear tree and refresh data
            self.tree.delete(*self.tree.get_children())
            self.module.create_message("userdata")
        else:
            print("No item selected.")

    def show_command_gui(self):
        self.destroy_widgets()
        self.create_command_widgets()

    def show_login_gui(self):
        self.destroy_widgets()
        self.create_login_widgets()

    def show_signup_gui(self):
        self.destroy_widgets()
        self.create_signup_widgets()

    def show_help_text(self):
        # The multiline string with commands and descriptions
        commands_description = """These are the commands:
> ls -f  lists files stored in server
> ls -a  lists all usernames
> ls -o  lists all users currently online
> ls -p  lists all users and their authorisation level
> delete  filename.extension deletes file called filename.extension if it exists
> add username password  adds username and password of authorization level user
> remove username  if authorized removes deletes account of 'username'
> userdata  lists all users and their authorization level
> privilege username  if authorized changes authorization level of account 'username'
> clear  clears output text box"""

        # Add the text to the Text widget
        self.output_text.insert(tk.END, commands_description)

        # Apply different colors to specific parts of the text
        self.output_text.tag_configure("green", foreground="green")

        # Find each command and parameters, and apply the "green" tag to the first instance
        for command in ["ls -f", "ls -a", "ls -o", "ls -p", "delete", "add", "remove", "userdata", "privilege", "clear"]:
            start_index = "1.0"
            start_index = self.output_text.search(command, start_index, stopindex=tk.END)
            if start_index:
                end_index = f"{start_index}+{len(command)}c"
                self.output_text.tag_add("green", start_index, end_index)

    def on_close(self):
        # Call the client's stop method when the GUI is closed
        try:
            self.client.stop()
        except:
            pass
        self.destroy()

    def login(self):
        user = self.user_entry.get()
        password = self.password_entry.get()

        if user and password:
            if self.module.login(user, password):
                self.show_command_gui()
            else:
                self.show_popup_message("Login failed.")
        else:
            self.show_popup_message("Username and password are required.")

    def show_popup_message(self, message):
        messagebox.showinfo("Popup Message", message)

    def send_command(self):
        user_input = self.input_entry.get()
        self.input_entry.delete(0, tk.END)
        if user_input:
            if user_input == "clear":
                self.output_text.delete("1.0", tk.END)
            elif user_input == "help":
                self.show_help_text()
            else:
                self.module.create_message(user_input)
        else:
            self.show_popup_message("Please enter a command")
    
    def create_user(self):
        if self.confirm_password_entry.get() == self.password_entry.get():
            self.module.create_message(f"add {self.user_entry.get()} {self.password_entry.get()}")
            self.show_login_gui()
        else:
            self.show_popup_message("Password mismatch. Try again.")

    def destroy_widgets(self):
        for widget in self.winfo_children():
            widget.destroy()

    def start(self):
        self.mainloop()

    def handle_response(self, response):
        try:
            self.output_text.insert(tk.END, response + "\n")
        except:
            pass

        