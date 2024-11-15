# apps.py
from django.apps import AppConfig
import os
import discord
import ccxt
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI  # Updated import
import re  # For regular expressions to extract possible crypto names

class GptConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gpt'
    bot_initialized = False  # Flag to track bot initialization

    def ready(self):
        load_dotenv()
        print("App is ready. Checking bot initialization.")
        DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
        BINANCE_SECRET = os.getenv('BINANCE_SECRET')
        DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

        if not self.bot_initialized:
            print("Starting Discord bot from apps...")
            # Initialize OpenAI client
            client = OpenAI(api_key=OPENAI_API_KEY)

            # Initialize Discord bot with proper intents
            intents = discord.Intents.default()
            intents.messages = True
            intents.message_content = True
            self.bot = commands.Bot(command_prefix="!", intents=intents)

            # Initialize Binance exchange connection
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'apiKey': BINANCE_API_KEY,
                'secret': BINANCE_SECRET
            })

            # Crypto symbol mapping for natural language queries
            self.crypto_symbol_mapping = {
                "bitcoin": "BTC/USDT",
                "btc": "BTC/USDT",
                "ethereum": "ETH/USDT",
                "eth": "ETH/USDT",
                "uniswap": "UNI/USDT",
                "uni": "UNI/USDT",
                "ripple": "XRP/USDT",
                "xrp": "XRP/USDT",
                "litecoin": "LTC/USDT",
                "ltc": "LTC/USDT",
                "cardano": "ADA/USDT",
                "ada": "ADA/USDT",
                "polkadot": "DOT/USDT",
                "dot": "DOT/USDT",
                "chainlink": "LINK/USDT",
                "link": "LINK/USDT",
                "dogecoin": "DOGE/USDT",
                "doge": "DOGE/USDT",
                "stellar": "XLM/USDT",
                "xlm": "XLM/USDT",
                "shiba inu": "SHIB/USDT",
                "shib": "SHIB/USDT",
                "avalanche": "AVAX/USDT",
                "avax": "AVAX/USDT",
                "solana": "SOL/USDT",
                "sol": "SOL/USDT",
                "tron": "TRX/USDT",
                "trx": "TRX/USDT",
                "bitcoin cash": "BCH/USDT",
                "bch": "BCH/USDT",
                "vechain": "VET/USDT",
                "vet": "VET/USDT",
                "filecoin": "FIL/USDT",
                "fil": "FIL/USDT",
                "matic": "MATIC/USDT",
                "polygon": "MATIC/USDT",
                "quant": "QNT/USDT",
                "bore": "BORA/USDT",
                # Add more mappings as needed
            }

            # Set the flag to indicate the bot is initialized
            self.bot_initialized = True

            # Function to extract symbol from user message
            def extract_crypto_symbol(content):
                # Try to match a well-known crypto symbol or name in the message
                for name, symbol in self.crypto_symbol_mapping.items():
                    if re.search(rf"\b{name}\b", content, re.IGNORECASE):
                        return symbol
                return None  # Return None if no match is found

            # Function to fetch market data from Binance
            def get_market_data(symbol):
                try:
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=1)
                    last_candle = ohlcv[-1]
                    price = last_candle[4]  # The close price
                    return {
                        'symbol': symbol,
                        'close_price': price,
                    }
                except Exception as e:
                    print(f"Error fetching market data for {symbol}: {str(e)}")
                    return None

            # Function to dynamically generate a response using ChatGPT
            def get_chatgpt_response(message_content, market_data=None):
                print("Using GPT 3.5 Model")
                gpt_prompt = f"Respond to this message as an expert in finance and crypto trading: {message_content}"
                if market_data:
                    gpt_prompt += f" The current price for {market_data['symbol']} is {market_data['close_price']} USD."

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": gpt_prompt}],
                    max_tokens=200
                )
                print("Response received from GPT.")

                return response.choices[0].message.content.strip()

            # Event handler when a message is sent (server or DM)
            @self.bot.event
            async def on_message(message):
                if message.author == self.bot.user:
                    print("Ignoring message from the bot itself.")
                    return  # Ignore messages from the bot itself
            
                try:
                    # Process commands first
                    await self.bot.process_commands(message)
            
                    # Only handle messages if they don't contain commands
                    if message.content.startswith(self.bot.command_prefix):
                        print("Message is a command. Ignoring for dynamic response.")
                        return  # Ignore messages that are commands
            
                    # Only proceed if the message is from a DM or the specified channel
                    if isinstance(message.channel, discord.DMChannel):
                        print("Handling DM message.")
                        await handle_message(message, is_dm=True)
                    elif message.channel.id == DISCORD_CHANNEL_ID:
                        print(f"Handling message in the allowed channel with ID {DISCORD_CHANNEL_ID}.")
                        await handle_message(message, is_dm=False)
                    else:
                        # Ignore messages from other channels
                        print(f"Ignoring message from channel with ID {message.channel.id}.")
                        return
            
                except Exception as e:
                    print(f"Error in on_message: {str(e)}")
                    await message.channel.send(f"An error occurred: {str(e)}")

            # Handle user messages dynamically
            async def handle_message(message, is_dm=False):
                print(f"Handling message: '{message.content}', is DM: {is_dm}")
                try:
                    content = message.content.lower()

                    # Check if the user is asking for a crypto price
                    if "price" in content or "what is" in content:
                        print("User is asking for a price or info.")
                        # Try to extract the crypto symbol from the message
                        symbol = extract_crypto_symbol(content)
                        
                        if symbol:
                            market_data = get_market_data(symbol)
                            if market_data:
                                # Get a refined response from GPT after fetching the price
                                gpt_response = get_chatgpt_response(message.content, market_data)
                                await message.channel.send(gpt_response)
                            else:
                                await message.channel.send(f"Sorry, I couldn't fetch data for {symbol}.")
                        else:
                            await message.channel.send("At this moment, I can't provide real-time data concerning that token. You can check a cryptocurrency exchange or financial news website for the latest price. If you have questions about crypto or finance in general, feel free to ask!")
                    else:
                        # If it's not a price-related query, fall back to the general GPT response
                        gpt_response = get_chatgpt_response(message.content)
                        await message.channel.send(gpt_response)

                except Exception as e:
                    print(f"Error in handle_message: {str(e)}")
                    await message.channel.send(f"An error occurred: {str(e)}")

            # Directly run the Discord bot
            print("Running Discord bot...")
            self.bot.run(DISCORD_TOKEN)

        else:
            print("Discord bot already initialized.")
