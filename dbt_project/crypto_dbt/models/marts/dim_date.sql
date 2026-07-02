{{ config(materialized='table') }}

with date_range as (
    select cast(fetched_at as date) as date_day
    from {{ ref('stg_crypto_prices') }}
    group by cast(fetched_at as date)
)

select
    date_day,
    extract(year from date_day) as year,
    extract(month from date_day) as month,
    extract(day from date_day) as day,
    extract(dayofweek from date_day) as day_of_week,
    format_date('%A', date_day) as day_name,
    format_date('%B', date_day) as month_name,
    extract(quarter from date_day) as quarter
from date_range