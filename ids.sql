-- name: all_lunaid
select * from enroll natural join person where etype like 'LunaID'

-- name: name_search
select
 fullname,lunaid,curagefloor,dob,sex,lastvisit,maxdrop,studies,pid
 from person_search_view
 where fullname like %(fullname)s
 limit 10

-- name: visit_by_pid
select
 to_char(vtimestamp,'YYYY-MM-DD'), study, vtype, vscore, age, note, dvisit,dperson,vid
 from visit_summary
  where pid = %(pid)s
  -- and "action" = 'checkedin'
  order by vtimestamp desc


-- name: contact_by_pid
select
  who,cvalue, relation, nogood, added, cid
  from contact
  where pid = %(pid)s
  order by relation, who
