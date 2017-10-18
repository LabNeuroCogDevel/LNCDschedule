-- name: all_lunaid
select * from enroll natural join person where etype like 'LunaID'

-- name: name_search
select
 fullname,lunaid,curagefloor,dob,sex,lastvisit,maxdrop,studies
 from person_search_view
 where fullname like %(fullname)s
 limit 10
