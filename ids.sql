-- name: all_lunaid
select * from enroll natural join person where etype like 'LunaID'

-- name: name_search
select
 fullname,lunaid,curagefloor,dob,sex,lastvisit,maxdrop,studies,pid
 from person_search_view
 where fullname ilike %(fullname)s
 limit 20

-- name: lunaid_search
select
 fullname,lunaid,curagefloor,dob,sex,lastvisit,maxdrop,studies,pid
 from person_search_view
 where lunaid = %(lunaid)s
 limit 10

-- name: att_search
-- N.B. ~ '' == like '%'
select
 fullname,lunaid,curagefloor,dob,sex,lastvisit,maxdrop,studies,pid
 from person_search_view
 where studies::text ~ %(study)s
   and sex like %(sex)s
   and curage >= %(minage)s
   and curage <= %(maxage)s
 limit 100
-- studies ? %(study)s

-- name: visit_by_pid
select
 to_char(vtimestamp,'YYYY-MM-DD'), study, vtype, vscore, age, note, dvisit,dperson,vid
 from visit_summary
  where pid = %(pid)s
  -- and "action" = 'checkedin'
  order by vtimestamp desc

-- name: note_by_pid
select note,dropcode, ndate, vtimestamp, note.ra, vid from note 
   natural left  join visit_note natural left join visit
   natural left join dropped
   where pid = %(pid)s
   order by vtimestamp desc, ndate desc 


-- name: contact_by_pid
select
  who,cvalue, relation, nogood, added, cid
  from contact
  where pid = %(pid)s
  order by relation = 'Subject' desc, relation, who

--name: list_studies
-- we want to sort studies by the last checkin
-- but we need to left join incase we have a (new) study with no visits
with vs as (
  select max(vtimestamp) latest, study from visit natural join visit_study group by study 
)
select study from study
 natural left join vs
 order by latest desc

--name: list_vtypes
select distinct(vtype) from visit;

--name: list_sources
select distinct("source") from person

--name: list_ctype
select distinct(ctype) from contact;

--name: list_relation
select distinct(relation) from contact;

