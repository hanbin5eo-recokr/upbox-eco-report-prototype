with base_company as (
    select id as company_id
         , customer_category_detail
    from prep_marts.l0ub20_company
    where 1 = 1
      and is_active = true
      and property_detail = 10
      and customer_category_detail = 501
)
   , base_contract as (
    select date_trunc('month', cdt.schedule_date)                                      as base_date
         , c.customer_company_id as company_id
         , cdt.contract_id
         , if(c.waste_type_detail in ('51-38-01', '91-02-00'), '음식물류', mcwi.waste_item_group) as waste_item_group
         , if(c.waste_type_detail in ('51-38-01', '91-02-00'), '음식물', mcwi.waste_item) as waste_item
         , if(c.waste_type_detail in ('51-38-01', '91-02-00'), '음식물', mcwi.waste_item_detail) as waste_item_detail
         , cdt.vol_amount
    from prep_marts.l1ub20_contract_daily_task_stats cdt
             join prep_marts.l0ub20_contract c on c.id = cdt.contract_id
             left join prep_marts.l0gsheet_map_contract_waste_item mcwi on mcwi.contract_id = cdt.contract_id
    where 1 = 1
      and cdt.task_category = 20
)
-- select * from base_contract where company_id in (5827, 6165); -- null 미존재
   , summary_contract as (
    select row_number() over (partition by bc.company_id order by bc.base_date desc) as rn
         , bc.base_date
         , bc.company_id
         , bc2.customer_category_detail
         , waste_item_group
         , waste_item
         , waste_item_detail
         , sum(bc.vol_amount) as amount
    from base_contract bc
             join base_company bc2 on bc.company_id = bc2.company_id
    group by 2, 3, 4, 5, 6, 7
)

   , summary_busi_amount as ( -- 업종 별 집계량
    select company_id
         -- , customer_category_detail
         , waste_item_group
         , waste_item
         , waste_item_detail
         , avg(amount) as avg_amount
    from summary_contract
    where 1=1
      and amount != 0
    and rn between 1 and 12
group by 1, 2, 3, 4
    )
select b.waste_item_group
    , b.waste_item
    , b.waste_item_detail
    , b.company_id as customer_company_id
    , c.name as customer_company_name
    , b.avg_amount as avg_mnthly_amount
    , if(b.company_id = 6286, 1, 0) as tgt_customer_flag
from summary_busi_amount b
left join prep_marts.l0ub20_company c on (c.id = b.company_id)
order by 1,2,3, b.avg_amount desc;