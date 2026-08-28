with source as (
    select * from {{ source('raw', 'raw_ebay_listings') }}
),

cleaned as (
    select
        listingid,
        cast(regexp_replace(raw_price, '[^0-9.]', '', 'g') as numeric)
            as price_usd,
        -- Clean currency strings (e.g., '$15.99' -> 15.99)
        created_at,
        trim(raw_title) as listing_title,
        -- Extract Strikethrough Price (looks for element with 'strikethrough' in classes)
        to_date(
            trim(regexp_replace(raw_sold_date, '^Sold[\s\xa0]+', '')),
            'Mon DD, YYYY'
        ) as sold_date,
        -- Extract Shipping Cost (handles "+$10.20 delivery" as well as "Free delivery")
        (
            select cast(regexp_replace(elem ->> 'text', '[^0-9.]', '', 'g') as numeric)
            from jsonb_array_elements(cast(raw_attributes as jsonb)) as elem
            where elem -> 'classes' @> cast('["strikethrough"]' as jsonb)
            limit 1
        ) as original_price_usd,
        (
            select
                case
                    when lower(elem ->> 'text') like '%free%' then 0.00
                    else
                        cast(
                            nullif(
                                regexp_replace(
                                    elem ->> 'text', '[^0-9.]', '', 'g'
                                ),
                                ''
                            ) as numeric
                        )
                end
            from jsonb_array_elements(cast(raw_attributes as jsonb)) as elem
            where
                elem ->> 'text' ilike '%delivery%'
                or elem ->> 'text' ilike '%shipping%'
            limit 1
        ) as shipping_cost_usd,
        coalesce(lower(
            raw_title) like '%magazine%', false) as
        is_magazine,
        coalesce(lower(
            raw_title) like '% cd %', false) as
        is_cd
    from source
)

select * from cleaned
