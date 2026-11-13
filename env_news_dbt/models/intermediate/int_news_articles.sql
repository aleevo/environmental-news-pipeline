
with staging as (

    select *
    from {{ ref('stg_news_articles') }}

),

classified as (

    select
        source,
        lower(trim(source)) as source_normalized,

        case
            when lower(trim(source)) = 'mongabay'
                then 'environmental_journalism'
            when lower(trim(source)) = 'dialogue_earth'
                then 'environmental_journalism'
            when lower(trim(source)) = 'sciencedaily'
                then 'science_news'
            when lower(trim(source)) = 'nasa'
                then 'government_science_agency'
            when lower(trim(source)) in ('eea', 'ec_eu')
                then 'government_environmental_organization'
            when lower(trim(source)) in ('dw', 'cgtn_china')
                then 'international_news_media'
            when lower(trim(source)) = 'carbon_brief'
                then 'climate_journalism'
            when lower(trim(source)) = 'clean_energy_wire'
                then 'energy_journalism'
            else 'other'
        end as source_category,

        title,
        summary,
        clean_url,
        published_at,
        published_at_ts,
        published_date,
        ingested_at

    from staging

),

final as (

    select
        source,
        source_normalized,
        source_category,
        title,
        summary,
        clean_url,
        published_at,
        published_at_ts,
        published_date,

        extract(year from published_date)::integer
            as publication_year,

        extract(month from published_date)::integer
            as publication_month,

        current_date - published_date
            as article_age_days,

        ingested_at

    from classified

)

select *
from final
