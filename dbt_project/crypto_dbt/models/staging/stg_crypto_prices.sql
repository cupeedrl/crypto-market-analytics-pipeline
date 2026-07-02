{{ config(materialized='view') }}

select
    id, coin_id, coin_name, symbol, current_price, market_cap, total_volume,
    price_change_24h, price_change_percent_24h, fetched_at,
    case when current_price > 0 then true else false end as is_valid_price,
    case when total_volume >= 0 then true else false end as is_valid_volume
from {{ source('crypto_ods', 'ods_daily_metrics') }}