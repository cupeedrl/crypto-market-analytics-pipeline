# Discord Bot Commands

## Overview

The Discord bot provides an interactive interface for users to query real-time market data and manage alert subscriptions directly within Discord.

![Discord Bot](../images/discord_bot.png)

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/price [symbol]` | Fetches the current live price and 24h change for a specific coin. | `/price BTC` |
| `/summary` | Displays a market overview including top gainers, losers, and total volume. | `/summary` |
| `/help` | Shows available commands and usage instructions. | `/help` |

## Why a Discord Bot?

While webhooks are sufficient for one-way notifications, a bot enables **bi-directional communication**.

**Key advantages:**
- **On-demand queries**: Users can check prices without leaving Discord.
- **Personalization**: Users can subscribe to specific coin alerts.
- **Interactivity**: Slash commands provide a structured, validated input method, reducing user errors compared to text parsing.

## Integration Architecture

The bot is built using `discord.py` and connects to the PostgreSQL database.

**Data Flow:**
1. User invokes `/price BTC`.
2. Bot validates input and queries `real_time_prices` table.
3. Bot formats response into an Embed and sends it to the channel.

**Why direct DB query?**
- **Latency**: Avoids an extra API call to the dashboard backend.
- **Simplicity**: Reduces infrastructure complexity by reusing the existing read replica.

## Challenges

### Rate Limits
Discord enforces strict rate limits (5 requests/2 seconds per channel).
**Solution**: Implemented a global cooldown and response caching for frequently requested coins (TTL: 10 seconds).

### Permissions
Bot requires specific permissions (Send Messages, Embed Links, Use Slash Commands).
**Solution**: Documented required permissions in the setup guide and implemented graceful degradation if permissions are missing.

## Future Improvements

- **Portfolio Tracking**: `/portfolio` command to track user holdings.
- **Natural Language Processing**: Allow queries like "What is the price of Bitcoin?" instead of strict slash commands.
- **Interactive Charts**: Generate and send Plotly charts directly in Discord.
