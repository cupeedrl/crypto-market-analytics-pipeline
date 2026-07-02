from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import psycopg2
import sys
import os
import discord

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.config import Config
from src.utils.logger import get_logger
from src.processing.indicators import analyze_coin

logger = get_logger(__name__)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def get_db_connection():
    return psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        database=Config.POSTGRES_DB
    )

async def send_discord_report(embed):
    """Send report via Discord bot"""
    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Client(intents=intents)
    
    @bot.event
    async def on_ready():
        try:
            channel = bot.get_channel(int(Config.DISCORD_CHANNEL_ID))
            if channel:
                await channel.send(embed=embed)
                logger.info("Daily report sent to Discord")
            await bot.close()
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            await bot.close()
    
    await bot.start(Config.DISCORD_BOT_TOKEN)

def generate_daily_report(**kwargs):
    """Generate daily market report"""
    import asyncio
    
    conn = get_db_connection()
    
    # Get all coins data
    query = """
        SELECT DISTINCT ON (symbol) 
            symbol, current_price, price_change_percent,
            volume, processed_at
        FROM real_time_prices
        ORDER BY symbol, processed_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        logger.warning("No data for daily report")
        return
    
    # Calculate statistics
    avg_change = df['price_change_percent'].mean()
    total_volume = df['volume'].sum()
    
    gainers = df.nlargest(3, 'price_change_percent')
    losers = df.nsmallest(3, 'price_change_percent')
    most_active = df.nlargest(3, 'volume')
    
    # Generate indicators for top coins
    top_coins_analysis = []
    for symbol in ['BTC', 'ETH', 'BNB']:
        coin_df = df[df['symbol'] == symbol]
        if not coin_df.empty:
            indicators = analyze_coin(coin_df)
            top_coins_analysis.append({
                'symbol': symbol,
                'price': indicators['current_price'],
                'signal': indicators['signal'],
                'trend': indicators['trend'],
                'rsi': indicators['rsi']
            })
    
    # Format report date
    report_date = datetime.now().strftime('%Y-%m-%d')
    
    # Create Discord Embed
    embed = discord.Embed(
        title=f"📊 Daily Crypto Report",
        description=f"**{report_date}** | Market Overview",
        color=discord.Color.blue()
    )
    
    # Market Overview Section
    overview_text = f"""
**Average Change:** {avg_change:+.2f}%
**Total Volume:** ${total_volume:,.0f}
**Active Coins:** {len(df)}
"""
    embed.add_field(name="📈 Market Overview", value=overview_text, inline=False)
    
    # Top Gainers Section
    if not gainers.empty:
        gainers_text = ""
        for idx, (_, row) in enumerate(gainers.iterrows(), 1):
            gainers_text += f"**{idx}.** `{row['symbol']}` — **{row['price_change_percent']:+.2f}%**\n"
        embed.add_field(name="🚀 Top Gainers (24h)", value=gainers_text, inline=True)
    
    # Top Losers Section
    if not losers.empty:
        losers_text = ""
        for idx, (_, row) in enumerate(losers.iterrows(), 1):
            losers_text += f"**{idx}.** `{row['symbol']}` — **{row['price_change_percent']:+.2f}%**\n"
        embed.add_field(name="📉 Top Losers (24h)", value=losers_text, inline=True)
    
    # Most Active Section
    if not most_active.empty:
        active_text = ""
        for idx, (_, row) in enumerate(most_active.iterrows(), 1):
            active_text += f"**{idx}.** `{row['symbol']}` — ${row['volume']:,.0f}\n"
        embed.add_field(name="🔥 Most Active", value=active_text, inline=True)
    
    # Technical Analysis Section
    if top_coins_analysis:
        analysis_text = ""
        for coin in top_coins_analysis:
            # Signal emoji mapping
            signal_emoji = {
                'STRONG_BUY': '🟢',
                'BUY': '🟢',
                'HOLD': '🟡',
                'SELL': '🔴',
                'STRONG_SELL': '🔴'
            }.get(coin['signal'], '⚪')
            
            # Format RSI with color indicator
            rsi_status = "🟢" if coin['rsi'] < 30 else ("🔴" if coin['rsi'] > 70 else "🟡")
            
            analysis_text += f"""
**{coin['symbol']}** {signal_emoji}
└ Signal: `{coin['signal']}` | Trend: `{coin['trend']}`
└ RSI: {rsi_status} {coin['rsi']:.1f}
"""
        
        embed.add_field(name="🎯 Technical Analysis", value=analysis_text, inline=False)
    
    # Footer
    embed.set_footer(text=f"Generated at {datetime.now().strftime('%H:%M')} UTC")
    
    # Send via Discord
    asyncio.run(send_discord_report(embed))
    
    logger.info("Daily report sent successfully")
    
    return {'report_generated': True}

with DAG(
    'crypto_daily_report',
    default_args=default_args,
    description='Daily crypto market report via Discord',
    schedule_interval='0 8 * * *',  # 8 AM UTC daily
    start_date=datetime(2026, 6, 28),
    catchup=False,
    tags=['reporting', 'discord']
) as dag:
    
    generate_report = PythonOperator(
        task_id='generate_daily_report',
        python_callable=generate_daily_report,
    )
    
    generate_report