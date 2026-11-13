with source_data as (

    select
        source,
        title,
        summary,
        clean_url,
        published_at,
        ingested_at
    from {{ source('landing', 'news_articles') }}

),

cleaned as (

    select
        source,
        title,
        summary,
        clean_url,
        published_at,
        ingested_at,

        case
            when btrim(published_at) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
                then null
            else nullif(btrim(published_at), '')::timestamptz
        end as published_at_ts,

        case
            when btrim(published_at) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
                then btrim(published_at)::date
            else nullif(btrim(published_at), '')::timestamptz::date
        end as published_date

    from source_data

)

select *
from cleaned
