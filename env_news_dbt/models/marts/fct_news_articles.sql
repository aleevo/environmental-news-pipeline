
with intermediate as (

    select *
    from {{ ref('int_news_articles') }}

),

final as (

    select
        clean_url,
        title,
        summary,

        source,
        source_normalized,
        source_category,

        publisher_name,
        publisher_base_country,
        publisher_base_continent,

        published_date,
        published_at_ts,

        publication_year,sss
        publication_month,

        article_age_days,
        ingested_at

    from intermediate

)

select *
from final
