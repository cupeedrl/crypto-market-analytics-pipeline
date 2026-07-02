import discord
from discord import app_commands
from discord.ext import commands, tasks
import pandas as pd
import psycopg2
from datetime import datetime, timedelta, time
from src.utils.config import Config
from src.utils.logger import get_logger
from src.processing.indicators import analyze_coin
import sqlalchemy

logger = get_logger(__name__)

# Intents cần thiết
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

def get_db_engine():
    """Tạo SQLAlchemy engine"""
    return sqlalchemy.create_engine(
        f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}"
        f"@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
    )

def normalize_symbol(coin: str) -> str:
    """Chuẩn hóa symbol: BTC -> BTCUSDT"""
    coin_upper = coin.upper().strip()
    if not coin_upper.endswith('USDT'):
        coin_upper = coin_upper + 'USDT'
    return coin_upper

@bot.event
async def on_ready():
    logger.info(f'Discord Bot logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
        
        # Start daily report task nếu chưa chạy
        if not daily_report.is_running():
            daily_report.start()
            logger.info("Daily report task started")
            
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

@bot.tree.command(name="price", description="Get price and indicators for a coin")
@app_commands.describe(coin="Coin symbol (e.g., BTC, ETH, SOL)")
async def price(interaction: discord.Interaction, coin: str = "BTC"):
    try:
        await interaction.response.defer()
        
        symbol = normalize_symbol(coin)
        logger.info(f"Querying price for: {symbol}")
        
        engine = get_db_engine()
        query = """
            SELECT current_price, price_change_percent, volume, processed_at
            FROM real_time_prices
            WHERE symbol = %s
            ORDER BY processed_at DESC
            LIMIT 100
        """
        df = pd.read_sql_query(query, engine, params=(symbol,))
        
        if df.empty:
            await interaction.followup.send(
                f"❌ No data for {symbol}\n\n"
                f"Available: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, DOT, AVAX, MATIC, LINK, LTC, UNI, ATOM, ETC"
            )
            return
        
        latest = df.iloc[0]
        
        # Handle NULL values
        current_price = latest['current_price'] if pd.notna(latest['current_price']) else 0
        price_change = latest['price_change_percent'] if pd.notna(latest['price_change_percent']) else 0
        volume = latest['volume'] if pd.notna(latest['volume']) else 0
        
        # Analyze
        try:
            indicators = analyze_coin(df)
            signal = indicators.get('signal', 'HOLD') or 'HOLD'
            trend = indicators.get('trend', 'UNKNOWN') or 'UNKNOWN'
            rsi = indicators.get('rsi', 50) or 50
            sma_20 = indicators.get('sma_20', current_price) or current_price
            sma_50 = indicators.get('sma_50', current_price) or current_price
        except Exception as e:
            logger.error(f"Error analyzing: {e}")
            signal = 'HOLD'
            trend = 'UNKNOWN'
            rsi = 50
            sma_20 = current_price
            sma_50 = current_price
        
        emoji = {
            'STRONG_BUY': '🚀',
            'BUY': '📈',
            'HOLD': '➡️',
            'SELL': '📉',
            'STRONG_SELL': '💥'
        }.get(signal, '❓')
        
        embed = discord.Embed(
            title=f"💰 {symbol.replace('USDT', '')} Price Analysis",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Current Price", value=f"${current_price:,.2f}", inline=False)
        embed.add_field(name="24h Change", value=f"{price_change:+.2f}%", inline=True)
        embed.add_field(name="Volume", value=f"${volume:,.0f}", inline=True)
        
        embed.add_field(name="📊 Indicators", value="", inline=False)
        embed.add_field(name="RSI (14)", value=f"{rsi:.2f}", inline=True)
        embed.add_field(name="SMA (20)", value=f"${sma_20:,.2f}", inline=True)
        embed.add_field(name="SMA (50)", value=f"${sma_50:,.2f}", inline=True)
        
        embed.add_field(name="Trend", value=trend, inline=True)
        embed.add_field(name="Signal", value=f"{emoji} {signal}", inline=True)
        
        embed.set_footer(text=f"Updated: {datetime.now().strftime('%H:%M:%S')}")
        
        await interaction.followup.send(embed=embed)
        logger.info(f"Successfully sent price for {symbol}")
        
    except Exception as e:
        logger.error(f"Error in /price: {e}", exc_info=True)
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}")
        except:
            await interaction.response.send_message(f"❌ Error: {str(e)}")

@bot.tree.command(name="summary", description="Daily market summary")
async def summary(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
        
        engine = get_db_engine()
        query = """
            SELECT DISTINCT ON (symbol) 
                symbol, current_price, price_change_percent, volume
            FROM real_time_prices
            ORDER BY symbol, processed_at DESC
        """
        df = pd.read_sql_query(query, engine)
        
        if df.empty:
            await interaction.followup.send("❌ No data available")
            return
        
        # Convert to numeric và fill NULL
        df['price_change_percent'] = pd.to_numeric(df['price_change_percent'], errors='coerce').fillna(0)
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
        df['current_price'] = pd.to_numeric(df['current_price'], errors='coerce').fillna(0)
        
        gainers = df.nlargest(3, 'price_change_percent')
        losers = df.nsmallest(3, 'price_change_percent')
        active = df.nlargest(3, 'volume')
        
        embed = discord.Embed(
            title="📊 Daily Market Summary",
            color=discord.Color.gold()
        )
        
        gainers_text = "\n".join([
            f"• {row['symbol'].replace('USDT', '')}: {row['price_change_percent']:+.2f}%"
            for _, row in gainers.iterrows()
        ]) if not gainers.empty else "N/A"
        embed.add_field(name="🚀 Top Gainers", value=gainers_text, inline=True)
        
        losers_text = "\n".join([
            f"• {row['symbol'].replace('USDT', '')}: {row['price_change_percent']:+.2f}%"
            for _, row in losers.iterrows()
        ]) if not losers.empty else "N/A"
        embed.add_field(name="📉 Top Losers", value=losers_text, inline=True)
        
        active_text = "\n".join([
            f"• {row['symbol'].replace('USDT', '')}: ${row['volume']:,.0f}"
            for _, row in active.iterrows()
        ]) if not active.empty else "N/A"
        embed.add_field(name="🔥 Most Active", value=active_text, inline=True)
        
        embed.set_footer(text=f"Total coins: {len(df)}")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in /summary: {e}", exc_info=True)
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="help", description="Show available commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Crypto Bot Commands",
        description="Available commands:",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="/price <coin>", value="Get price + indicators\nExample: `/price BTC`", inline=False)
    embed.add_field(name="/summary", value="Daily market summary", inline=False)
    embed.add_field(name="/help", value="Show this message", inline=False)
    embed.add_field(name="Coins", value="BTC, ETH, BNB, SOL, XRP, ADA, DOGE, DOT, AVAX, MATIC, LINK, LTC, UNI, ATOM, ETC", inline=False)
    
    await interaction.response.send_message(embed=embed)

@tasks.loop(time=time(20, 0))  # 8h tối (20:00)
async def daily_report():
    """Gửi báo cáo daily tự động mỗi ngày lúc 8h sáng"""
    try:
        channel = bot.get_channel(int(Config.DISCORD_CHANNEL_ID))
        if not channel:
            logger.error(f"Discord channel {Config.DISCORD_CHANNEL_ID} not found")
            return
        
        engine = get_db_engine()
        
        # Query top gainers/losers
        query = """
            SELECT DISTINCT ON (symbol) 
                symbol, current_price, price_change_percent, volume
            FROM real_time_prices
            ORDER BY symbol, processed_at DESC
        """
        df = pd.read_sql_query(query, engine)
        
        if df.empty:
            logger.warning("No data for daily report")
            return
        
        # Convert to numeric
        df['price_change_percent'] = pd.to_numeric(df['price_change_percent'], errors='coerce').fillna(0)
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
        
        gainers = df.nlargest(5, 'price_change_percent')
        losers = df.nsmallest(5, 'price_change_percent')
        
        report_date = datetime.now().strftime('%Y-%m-%d')
        
        embed = discord.Embed(
            title=f"📊 End of Day Crypto Report - {report_date}",  # Đổi tên
            description="Daily market performance summary",  # Đổi description
            color=discord.Color.purple()
        )
                
        # Top Gainers
        gainers_text = "\n".join([
            f"• **{row['symbol'].replace('USDT', '')}**: {row['price_change_percent']:+.2f}% (${row['current_price']:,.2f})"
            for _, row in gainers.iterrows()
        ])
        embed.add_field(name="🚀 Top 5 Gainers", value=gainers_text or "N/A", inline=False)
        
        # Top Losers
        losers_text = "\n".join([
            f"• **{row['symbol'].replace('USDT', '')}**: {row['price_change_percent']:+.2f}% (${row['current_price']:,.2f})"
            for _, row in losers.iterrows()
        ])
        embed.add_field(name="📉 Top 5 Losers", value=losers_text or "N/A", inline=False)
        
        # Market Stats
        total_coins = len(df)
        avg_change = df['price_change_percent'].mean()
        embed.add_field(
            name="📈 Market Overview", 
            value=f"Total coins tracked: **{total_coins}**\nAverage change: **{avg_change:+.2f}%**",
            inline=False
        )
        
        embed.set_footer(text=f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await channel.send(embed=embed)
        logger.info(f"Daily report sent successfully at {datetime.now()}")
        
    except Exception as e:
        logger.error(f"Error sending daily report: {e}", exc_info=True)

def start_bot():
    """Start the Discord bot"""
    bot.run(Config.DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    start_bot()