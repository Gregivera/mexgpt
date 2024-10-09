# views.py

from django.http import HttpResponse
from django.views import View
import os
import discord
import threading
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Discord bot with proper intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

bot_initialized = False  # Flag to track if the bot has been initialized

class StartBotView(View):
    def get(self, request):
        global bot_initialized

        if not bot_initialized:
            threading.Thread(target=self.run_discord_bot, daemon=True).start()
            bot_initialized = True
            return HttpResponse("Discord bot is starting in the background.")
        else:
            return HttpResponse("Discord bot is already running.")

    def run_discord_bot(self):
        print("Starting Discord bot from views...")
        bot.run(DISCORD_TOKEN)

# Add your other bot event handlers and functions here
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Process your commands or custom handling here
    await bot.process_commands(message)

# You can also add more event handlers and functions as needed.