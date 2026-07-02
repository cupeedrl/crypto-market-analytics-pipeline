{{ config(materialized='table') }}

select
    m.id as metric_id,
    m.coin_id,
    d.coin_name,
    d.symbol,
    m.current_price,
    m.market_cap,
    m.total_volume,
    m.price_change_24h,
    m.price_change_percent_24h,
    m.fetched_at,
    cast(m.fetched_at as date) as date_day,
    
    case 
        when m.price_change_percent_24h > 5 then 'high_increase'
        when m.price_change_percent_24h < -5 then 'high_decrease'
        else 'normal'
    end as price_volatility_category

from {{ ref('stg_crypto_prices') }} m
left join {{ ref('dim_coin') }} d on m.coin_id = d.coin_id
where m.is_valid_price = true
  and m.is_valid_volume = true