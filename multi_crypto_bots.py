import discord
from discord import app_commands
import asyncio
import requests

CREDITS = "wyatt09330_08175"

# 🔹 PUT YOUR SERVER (GUILD) ID HERE FOR INSTANT / COMMANDS
GUILD_ID = 12345678910  # <-- REPLACE THIS

# ================= BOT CONFIG =================
BOTS = [
    {"token": "Token", "status_coin": "bitcoin"},
    {"token": "Token", "status_coin": "ethereum"},
    {"token": "Token", "status_coin": "solana"},
    {"token": "Token", "status_coin": "pepe"},
]
# ==============================================

API_BASE = "https://api.coingecko.com/api/v3"
HEADERS = {
    "User-Agent": "DiscordCryptoBot/1.0"
}

def get_coin_data(coin_id):
    try:
        url = f"{API_BASE}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }

        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = r.json()

        if coin_id not in data:
            return None

        price = data[coin_id]["usd"]
        change = data[coin_id]["usd_24h_change"]

        return price, change

    except Exception as e:
        print("API error:", e)
        return None

async def run_bot(config):
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    async def update_status():
        await client.wait_until_ready()
        while not client.is_closed():
            data = get_coin_data(config["status_coin"])
            if not data:
                await asyncio.sleep(30)
                continue

            price, change = data
            coin = config["status_coin"].title()

            if change >= 0:
                status = f"🟢📈 {coin} +{change:.2f}% | ${price:,}"
            else:
                status = f"🔴📉 {coin} {change:.2f}% | ${price:,}"

            status += f" | {CREDITS}"

            await client.change_presence(
                activity=discord.Game(name=status)
            )

            await asyncio.sleep(60)

    @tree.command(name="coin", description="Get live stats for any coin")
    async def coin(interaction: discord.Interaction, name: str):
        coin_id = name.lower().strip()
        data = get_coin_data(coin_id)

        if not data:
            await interaction.response.send_message(
                f"❌ Coin `{coin_id}` not found or API error.",
                ephemeral=True
            )
            return

        price, change = data
        arrow = "📈" if change >= 0 else "📉"
        color = 0x00ff00 if change >= 0 else 0xff0000

        embed = discord.Embed(
            title=f"{coin_id.title()} Live Stats",
            color=color
        )
        embed.add_field(name="Price", value=f"${price:,}", inline=False)
        embed.add_field(name="24h Change", value=f"{arrow} {change:.2f}%", inline=False)
        embed.set_footer(text=f"Credits: {CREDITS}")

        await interaction.response.send_message(embed=embed)

    @client.event
    async def on_ready():
        guild = discord.Object(id=GUILD_ID)
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)

        print(f"Bot online as {client.user}")
        client.loop.create_task(update_status())

    await client.start(config["token"])

async def main():
    await asyncio.gather(*(run_bot(bot) for bot in BOTS))

asyncio.run(main())
