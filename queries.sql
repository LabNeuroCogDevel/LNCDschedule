-- name: all_lunaid
select * from enroll natural join person where etype like 'LunaID'

-- name: name_search
select
 fullname,lunaid,curagefloor,dob,sex,lastvisit,maxdrop,studies,pid
 from person_search_view
 where fullname ilike %(fullname)s and
 -- make null drop 'nodrop', for all default to search max(droplevels)=='family'
 coalesce(maxdrop,'nodrop'::droplevels) <= %(maxdrop)s and
 -- view makes no lunaid a lunaid of 0, for all search lunaid > -1
 coalesce(lunaid,0) > %(minlunaid)s and
 coalesce(lunaid,0) < %(maxlunaid)s
 limit 50

-- name: lunaid_search
select
 fullname,lunaid,curagefloor,dob,sex,lastvisit,maxdrop,studies,pid
 from person_search_view
 where lunaid = %(lunaid)s
 limit 10

-- name: subject_search
select 
  fullname,lunaid,curagefloor,dob,sex,lastvisit,maxdrop,studies,pid
from person_search_view 
where maxdrop is null;

-- name: get_everything
select 
  fullname,lunaid,curagefloor,dob,sex,lastvisit,maxdrop,studies,pid
from person_search_view 

--name: lunaid_search_all
select 
  fullname,lunaid,curagefloor,dob,sex,lastvisit,maxdrop,studies,pid
from person_search_view 
where lunaid >= %(lunaid)s;

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

--name: get_birthday
select
 to_char(dob,'YYYY-MM-DD')
 from visit_person_view
 where vid = %(vid)s
 
--name: update_uri
update visit
  set googleuri = %(googleuri)s
  where vid = %(vid)s

--name: update_age
update visit
  set age = %(age)s
  where vid = %(vid)s

--name: update_RA
update visit_action
  set ra = %(ra)s
  where vid = %(vid)s

--name: get_time
select  vtimestamp
from visit_summary
where vid = %(vid)s

-- name: visit_by_pid
select
 to_char(vtimestamp,'YYYY-MM-DD'), study, "action", vtype, vscore, age, note, dvisit,dperson,vid
 from visit_summary
  where pid = %(pid)s
  -- and "action" = 'checkedin'
  order by vtimestamp desc
  
-- name: get_googleuri
select
 googleuri
 from visit
 where vid = %(vid)s

-- name: visit_by_vid
select
 pid,study,vtype, "action", vscore, age, note, to_char(vtimestamp,'YYYY-MM-DD') 
 from visit_summary
  where vid = %(vid)s
  -- and "action" = 'checkedin'

-- name: cal_info_by_vid
select
 study, vtype, visitno, age, sex, concat_ws(' ',fname,lname), dur_hr, vtimestamp, note, ra, googleuri
 from visit_summary natural join person
 where vid = %(vid)s

-- name: note_by_pid
select note,dropcode, ndate, vtimestamp, note.ra, vid from note 
   natural left  join visit_note natural left join visit
   natural left join dropped
   where pid = %(pid)s
   order by vtimestamp desc, ndate desc 
--name: get_status
select vstatus
from visit_person_view
where pid = %(pid)s
and to_char(vtimestamp,'YYYY-mm-dd') = %(vtimestamp)s

-- name: contact_by_pid
select
  who,cvalue, relation, nogood, added, cid
  from contact
  where pid = %(pid)s
  order by relation = 'Subject' desc, relation, who

-- name: get_person
select
  fullname
  from person_search_view
  where pid = %(pid)s

-- name: get_vid
select
  pid
  from visit_summary
  where pid = %(pid)s

-- name: get_tasks
select
  task
  from visit_task
  where vid = %(vid)s
-- name: get_measures
select
  measures
  from visit_task
  where vid = %(vid)s
  and task = %(task)s

-- name: vdesc_from_pid
select
  vid, concat_ws(' ', to_char(vtimestamp,'YYYY-mm-dd'),  study, vtype) as vdesc
  from visit_summary
  where pid = %(pid)s
  order by vtimestamp desc

-- name: get_pid_of_visit
select
  pid, vid
  from visit_summary
  where vtimestamp = %(vtimestamp)s
    and study like %(study)s
    and floor(age)::int = %(age)s

-- name: get_nid
select 
  nid
  from note
  where pid = %(pid)s
    and note = %(note)s
    and ndate = %(ndate)s

-- name: delete_visit
  delete from visit
    where vid = %(vid)s


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
 

-- name: list_tasks_of_study_vtype
select distinct(task) from study_task
 natural join task
 where study ilike %(study)s
 and (  modes ? %(vtype)s or modes ? 'Questionnaire' ) 

-- name: list_ras
select distinct ra from ra;

-- name: list_dropcodes
select dropcode, droplevel from dropcode where droplevel !=  'nodrop' order by droplevel desc;
