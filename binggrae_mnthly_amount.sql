with base_company as (
    select id as company_id
         , customer_category_detail
    from prep_marts.l0ub20_company
    where 1 = 1
      and is_active = true
      and property_detail = 10
      and id = 6286
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
         , bc.waste_item_group
         , bc.waste_item
         , bc.waste_item_detail
         , sum(bc.vol_amount) as amount
    from base_contract bc
             join base_company bc2 on bc.company_id = bc2.company_id
    group by 2, 3, 4, 5, 6, 7
)
   , lag_amount as (
    select sc.base_date
         , sc.company_id
         , sc.customer_category_detail
         , sc.waste_item_group
         , sc.waste_item
         , sc.waste_item_detail
         , sc.amount
         , sc2.amount as ytd_amount
    from summary_contract sc
             left join (select * from summary_contract) sc2
                       on (sc.company_id = sc2.company_id and sc2.base_date = date_add('year', -1, sc.base_date)
                           and sc.customer_category_detail = sc2.customer_category_detail and sc.waste_item_detail = sc2.waste_item_detail)
)
-- Select * from lag_amount ;
select lc.base_date
--      , lc.company_id
--      , c.name as company_name
--      , lc.customer_category_detail as customer_category_detail_code
--      , cct.code_desc as customer_category_detail
     , lc.waste_item_group
     , lc.waste_item
     , lc.waste_item_detail
     , lc.amount as mnthly_amount
     , lc.ytd_amount as ly_mnthly_amount
     , ((lc.amount - lc.ytd_amount) / cast(lc.ytd_amount as double)) as yoy_growth
from lag_amount lc
         left join prep_marts.l0ub20_company c on lc.company_id = c.id
         left join prep_marts.l0ub20_common_code_table cct
                   on (lc.customer_category_detail = cct.code_value and cct.code_group = 'customer_category_detail')
where 1=1
order by 2,3,4,1
