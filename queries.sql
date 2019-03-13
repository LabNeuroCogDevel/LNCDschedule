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

--name: person_by_pid
select * from person_search_view where pid = %(pid)s 

--name: next_luna
select max(lunaid) from person_search_view where lunaid < 20000


-- name: visit_by_pid
select
 to_char(vtimestamp,'YYYY-MM-DD'), study, "action", vtype, vscore, age, note, dvisit,dperson,vid
 from visit_summary
  where pid = %(pid)s
  -- and "action" = 'checkedin'
  order by vtimestamp desc

-- name: visit_by_vid
select
 pid,study,vtype, "action", vscore, age, note, to_char(vtimestamp,'YYYY-MM-DD') 
 from visit_summary
  where vid = %(vid)s
  -- and "action" = 'checkedin'

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

-- name: get_vid
select
  pid
  from visit_summary
  where pid = %(pid)s

-- name: get_nid
select 
  nid
  from note
  where pid = %(pid)s
    and note = %(note)s
    and ndate = %(ndate)s


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

--name: all_tasks
-- collapse tasks into task, vtypes (space sep list, all have just one currently) , studies (space sep list)
with ts as (
  select 
   task, string_agg(distinct(study),' ') as studies 
   from study_task 
   group by task
 )
 select 
   task.task,
   studies,
   string_agg(vtypes,' ') as modes
  from task 
  natural join jsonb_array_elements_text(modes) as vtypes
  natural join ts
  group by task.task, studies
 

--name: list_tasks_of_study_vtype
select distinct(task) from study_task
 natural join task
 where study ilike %(study)s
 and (  modes ? %(vtype)s or modes ? 'Questionnaire' ) 