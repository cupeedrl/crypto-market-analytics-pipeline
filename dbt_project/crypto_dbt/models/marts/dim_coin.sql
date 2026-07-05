{{ config(materialized='table') }}

-- Get distinct coins from staging data
with distinct_coins as (
    select distinct coin_id
    from {{ ref('stg_crypto_prices') }}
),

-- Map coin_id to coin_name and symbol
coin_mapping as (
    select 'bitcoin' as coin_id, 'Bitcoin' as coin_name, 'BTC' as symbol union all
    select 'ethereum', 'Ethereum', 'ETH' union all
    select 'binancecoin', 'Binance Coin', 'BNB' union all
    select 'solana', 'Solana', 'SOL' union all
    select 'ripple', 'XRP', 'XRP' union all
    select 'usd-coin', 'USD Coin', 'USDC' union all
    select 'zcash', 'Zcash', 'ZEC' union all
    select 'celo', 'Celo', 'CELO' union all
    select 'nfp-token', 'NFP Token', 'NFP' union all
    select 'rlusd', 'RLUSD', 'RLUSD' union all
    select 're', 'RE', 'RE' union all
    select 'aigensyn', 'AIGENSYN', 'AIGENSYN' union all
    select 'gram', 'GRAM', 'GRAM' union all
    select 'stellar', 'Stellar', 'XLM' union all
    select 'near', 'NEAR Protocol', 'NEAR' union all
    select 'cardano', 'Cardano', 'ADA' union all
    select 'aave', 'Aave', 'AAVE' union all
    select 'usdp-stablecoin', 'USDP Stablecoin', 'USDP'
)

select
    dc.coin_id,
    cm.coin_name,
    cm.symbol,
    CURRENT_TIMESTAMP() as first_seen,
    CURRENT_TIMESTAMP() as last_updated
from distinct_coins dc
left join coin_mapping cm on dc.coin_id = cm.coin_id