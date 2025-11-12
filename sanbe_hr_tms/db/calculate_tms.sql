-- DROP PROCEDURE public.calculate_tms(int4, int4, int4);

CREATE OR REPLACE PROCEDURE public.calculate_tms(period integer, l_area integer, branch integer)
    LANGUAGE plpgsql
AS
$procedure$

begin


    ALTER TABLE hr_tmsentry_summary

        DISABLE TRIGGER ALL;


-- delete temp_hr_tmsentry_summary

    DELETE FROM temp_hr_tmsentry_summary;


-- delete temp_sb_tms_tmsentry_details

    DELETE FROM temp_sb_tms_tmsentry_details;

-- hapus table temporary

    DROP TABLE IF EXISTS temp_hr_tmsentry_summary;

    DROP TABLE IF EXISTS temp_sb_tms_tmsentry_details;


-- create table temporary with no data

    CREATE TABLE temp_hr_tmsentry_summary AS
        TABLE hr_tmsentry_summary
        WITH NO DATA;


    CREATE TABLE temp_sb_tms_tmsentry_details AS
        TABLE sb_tms_tmsentry_details
        WITH NO DATA;


-- insert to temp_hr_tmsentry_summary

    INSERT INTO temp_hr_tmsentry_summary

    SELECT distinct hts.*

    FROM hr_tmsentry_summary hts

             JOIN sb_tms_tmsentry_details sttd ON sttd.tmsentry_id = hts.id

    WHERE sttd.is_edited = TRUE

       or sttd.approved_by_ca = TRUE

       or sttd.approved = TRUE

/*AND sttd.approved = TRUE*/;


-- insert to temp_sb_tms_tmsentry_details

    INSERT INTO temp_sb_tms_tmsentry_details

    SELECT *

    FROM sb_tms_tmsentry_details sttd

    WHERE sttd.is_edited = TRUE

       or sttd.approved_by_ca = TRUE

       or sttd.approved = TRUE

/*AND sttd.approved = TRUE*/;


-- delete before procedure executed

    DELETE

    FROM sb_tms_tmsentry_details

    where tmsentry_id in
          (select id FROM hr_tmsentry_summary WHERE periode_id = period and area_id = l_area and branch_id = branch);


    DELETE FROM hr_tmsentry_summary WHERE periode_id = period and area_id = l_area and branch_id = branch;

    delete from sb_tms_tmsentry_details where tmsentry_id is null;


-- insert tms summary | header

    INSERT INTO hr_tmsentry_summary (employee_id, nik, employee_group1, job_id, periode_id, area_id, department_id,
                                     branch_id, state)

    SELECT he.id   as employee_id,

           he.nik,

           he.employee_group1,

           he.job_id,

           p.id    as period_id,

           he.area as area_id,

           he.department_id,

           he.branch_id,

           'draft' as state

    FROM hr_opening_closing p

             JOIN hr_employee he ON p.branch_id = he.branch_id AND p.area_id = he.area

    WHERE p.id = period

      and p.branch_id = branch

      and p.area_id = l_area

      and he.state = 'approved'

      and he.emp_status in ('probation', 'confirmed');


-- insert tms summary detail

    INSERT INTO sb_tms_tmsentry_details as sttd (tmsentry_id, employee_id, details_date, status, dayname)

    SELECT hts.id                                  as tmsentry_id,

           hts.employee_id,

           generate_series(open_periode_from::date, open_periode_to::date,
                           interval '1 day')::date AS period,

           'draft'                                 as status,

           to_char(generate_series(open_periode_from::date, open_periode_to::date, interval '1 day')::date,
                   'Day')                          AS dayname

    FROM hr_tmsentry_summary hts

             JOIN hr_opening_closing hoc
                  ON hts.periode_id = hoc.id and hts.area_id = hoc.area_id and hts.branch_id = hoc.branch_id

    where hts.periode_id = period

      and hts.area_id = l_area

      and hts.branch_id = branch;


-- update national holiday from calendar

    UPDATE sb_tms_tmsentry_details ha

    SET type = 'H'

    FROM hr_tmsentry_summary hts,

         resource_calendar_leaves rcl

    WHERE ha.tmsentry_id = hts.id

      AND hts.area_id = rcl.area_id

      AND hts.periode_id = period

      AND ha.details_date::date IN (SELECT generate_series(rcl.date_from::date, rcl.date_to::date, interval '1 day'))

      AND rcl.state = 'post'

      AND rcl.area_id = l_area;


-- update W , employee_id, empgroup, workingday

    WITH flag AS (SELECT 'W'                                                                               AS cf,

                         hed.employee_id,

                         generate_series(hed.valid_from::date, hed.valid_to::date, interval '1 day')::date AS wd,

                         to_char(generate_series(hed.valid_from::date, hed.valid_to::date, interval '1 day')::date,
                                 'FMDay')                                                                  AS day_name,

                         he.id                                                                             AS empgroup_id,

                         hed.wdcode,

                         hwd.fullday_from                                                                  AS schedule_timein,

                         hwd.fullday_to                                                                    AS schedule_timeout,

                         type_hari

                  FROM hr_empgroup he

                           JOIN hr_empgroup_details hed ON he.id = hed.empgroup_id

                           JOIN hr_working_days hwd ON hed.wdcode = hwd.id and hwd.type_hari <> 'shift'

                           join hr_opening_closing hoc on hoc.id = period and hoc.branch_id = branch and
                                                          hed.valid_from between hoc.open_periode_from and hoc.open_periode_to

                  WHERE he.branch_id = branch
                    AND he.state = 'approved'), -- Assuming 'branch' is a variable you replace during execution AND he.state = 'approved'),

         flags AS (SELECT *

                   FROM flag

                   WHERE day_name NOT IN ('Sunday')

                     AND type_hari = 'fhday'

                   UNION ALL

                   SELECT *

                   FROM flag

                   WHERE day_name NOT IN ('Sunday', 'Saturday')

                     AND type_hari = 'fday'

                   UNION ALL

                   SELECT *

                   FROM flag

                   WHERE type_hari NOT IN ('fhday', 'fday'))

    UPDATE sb_tms_tmsentry_details ha

    SET type              = f.cf,

        empgroup_id       = f.empgroup_id,

        workingday_id     = f.wdcode,

        schedule_time_in  = f.schedule_timein,

        schedule_time_out = f.schedule_timeout

    FROM hr_tmsentry_summary hts,

         flags f

    WHERE ha.tmsentry_id = hts.id

      AND hts.employee_id = f.employee_id

      AND hts.periode_id = period

      AND ha.details_date::date = f.wd

      AND ha.type IS NULL

      AND hts.area_id = l_area

      AND hts.branch_id = branch;


-- update W , employee_id, empgroup, workingday

    WITH flag AS (SELECT 'W'                                                                               AS cf,

                         hed.employee_id,

                         generate_series(hed.valid_from::date, hed.valid_to::date, interval '1 day')::date AS wd,

                         to_char(generate_series(hed.valid_from::date, hed.valid_to::date, interval '1 day')::date,
                                 'FMDay')                                                                  AS day_name,

                         he.id                                                                             AS empgroup_id,

                         hed.wdcode,

                         hwd.fullday_from                                                                  AS schedule_timein,

                         hwd.fullday_to                                                                    AS schedule_timeout,

                         type_hari

                  FROM hr_empgroup he

                           JOIN hr_empgroup_details hed ON he.id = hed.empgroup_id

                           JOIN hr_working_days hwd ON hed.wdcode = hwd.id and hwd.type_hari = 'shift'

                           join hr_opening_closing hoc
                                on hoc.id = period and hed.valid_from between hoc.open_periode_from and hoc.open_periode_to

                  WHERE he.branch_id = branch -- Assuming 'branch' is a variable you replace during execution

                    AND he.state = 'approved'),

         flags AS (SELECT *

                   FROM flag

                   WHERE day_name NOT IN ('Sunday')

                     AND type_hari = 'fhday'

                   UNION ALL

                   SELECT *

                   FROM flag

                   WHERE day_name NOT IN ('Sunday', 'Saturday')

                     AND type_hari = 'fday'

                   UNION ALL

                   SELECT *

                   FROM flag

                   WHERE type_hari NOT IN ('fhday', 'fday'))

    UPDATE sb_tms_tmsentry_details ha

    SET type              = f.cf,

        empgroup_id       = f.empgroup_id,

        workingday_id     = f.wdcode,

        schedule_time_in  = f.schedule_timein,

        schedule_time_out = f.schedule_timeout

    FROM hr_tmsentry_summary hts,

         flags f

    WHERE ha.tmsentry_id = hts.id

      AND hts.employee_id = f.employee_id

      AND hts.periode_id = period

      AND ha.details_date::date = f.wd

-- AND ha.type IS NULL

      AND hts.area_id = l_area

      AND hts.branch_id = branch;


-- update W , employee_id, empgroup, workingday

    WITH flag AS (SELECT 'W'                                                                               AS cf,

                         hed.employee_id,

                         generate_series(hed.valid_from::date, hed.valid_to::date, interval '1 day')::date AS wd,

                         to_char(generate_series(hed.valid_from::date, hed.valid_to::date, interval '1 day')::date,
                                 'FMDay')                                                                  AS day_name,

                         he.id                                                                             AS empgroup_id,

                         hed.wdcode,

                         hwd.halfday_from                                                                  AS schedule_timein,

                         hwd.halfday_to                                                                    AS schedule_timeout,

                         type_hari

                  FROM hr_empgroup he

                           JOIN hr_empgroup_details hed ON he.id = hed.empgroup_id

                           JOIN hr_working_days hwd ON hed.wdcode = hwd.id and hwd.type_hari = 'fhday'

                           join hr_opening_closing hoc
                                on hoc.id = period and hed.valid_from between hoc.open_periode_from and hoc.open_periode_to

                  WHERE he.branch_id = branch
                    AND he.state = 'approved'), -- Assuming 'branch' is a variable you replace during execution AND he.state = 'approved'),

         flags AS (SELECT *

                   FROM flag

                   WHERE day_name IN ('Saturday')

                     AND type_hari = 'fhday')

    UPDATE sb_tms_tmsentry_details ha

    SET schedule_time_in  = f.schedule_timein,

        schedule_time_out = f.schedule_timeout

    FROM hr_tmsentry_summary hts,

         flags f

    WHERE ha.tmsentry_id = hts.id

      AND hts.employee_id = f.employee_id

      AND hts.periode_id = period

      AND ha.details_date::date = f.wd

-- AND ha.type IS NULL

      AND hts.area_id = l_area

      AND hts.branch_id = branch;


-- insert data upload attendance ke tms details

    with flag as (SELECT dua.employee_id,

                         dua.nik,

                         dua.tgl        AS details_date,

                         dua.tgl_masuk  AS date_in,

                         dua.time_in,

                         dua.tgl_keluar AS date_out,

                         dua.time_out

                  FROM data_upload_attendance dua

                           JOIN hr_tmsentry_summary hts ON dua.employee_id = hts.employee_id)

    update sb_tms_tmsentry_details ha

    set date_in=f.date_in,

        time_in=f.time_in,

        date_out=f.date_out,

        time_out = f.time_out

    from hr_tmsentry_summary hts,

         flag f

    where hts.employee_id = f.employee_id

      and ha.tmsentry_id = hts.id

      and hts.periode_id = period

      and ha.details_date::date = f.details_date

      and hts.area_id = l_area

      and hts.branch_id = branch;


    --update time_in and time out with swap in out = True

-- with xx as (

-- select

-- distinct dua.employee_id,

-- dua.tgl,

-- dua.tgl_masuk,

-- dua.time_out time_in,

-- (dua.tgl_masuk + interval '1 day')::date tgl_keluar,

-- dua_next.time_in time_out

-- from sb_tms_tmsentry_details sttd

-- join hr_tmsentry_summary hts on sttd.tmsentry_id = hts.id

-- join hr_working_days hwd on sttd.workingday_id = hwd.id

-- join data_upload_attendance dua on sttd.employee_id = dua.employee_id

-- left join data_upload_attendance dua_next on dua.employee_id = dua_next.employee_id and dua_next.tgl_masuk = dua.tgl_masuk + interval '1 day'

-- where hwd.swap_in_out = True

-- and dua.tgl_masuk = dua.tgl_keluar

-- and dua.time_out > dua.time_in

-- )

-- update sb_tms_tmsentry_details sttd

-- set time_in = xx.time_in, date_out = xx.tgl_keluar, time_out = xx.time_out

-- from xx

-- where sttd.employee_id = xx.employee_id and sttd.details_date = xx.tgl;


--

--update sb_tms_tmsentry_details set aot4 = time_in where id in (select id from sb_tms_tmsentry_details where workingday_id in (select id from hr_working_days where swap_in_out = True));

-- update sb_tms_tmsentry_details set time_in = null where id in (select id from sb_tms_tmsentry_details where workingday_id in (select id from hr_working_days where swap_in_out = True));

-- update sb_tms_tmsentry_details set time_in = time_out where id in (select id from sb_tms_tmsentry_details where workingday_id in (select id from hr_working_days where swap_in_out = True));

-- update sb_tms_tmsentry_details set time_out = null where id in (select id from sb_tms_tmsentry_details where workingday_id in (select id from hr_working_days where swap_in_out = True));

-- update sb_tms_tmsentry_details ts set time_out = ss.aot4 , date_out = (ts.details_date + INTERVAL '1 day')::date

-- from

-- (select (details_date - INTERVAL '1 day')::date as details_date, aot4 , sb_tms_tmsentry_details.employee_id

-- from sb_tms_tmsentry_details where workingday_id in (select id from hr_working_days where swap_in_out = True) and aot4 is not null)ss

-- where ss.details_date = ts.details_date and ts.employee_id = ss.employee_id;

-- update sb_tms_tmsentry_details set aot4 = null where id in (select id from sb_tms_tmsentry_details where workingday_id in (select id from hr_working_days where swap_in_out = True));


--swap in out GH 3 Sep 2025


--swap in out GH 3 Sep 2025


    update sb_tms_tmsentry_details
    set aot4 = time_in
    where id in (select b.id
                 from hr_tmsentry_summary a
                          join sb_tms_tmsentry_details b
                               on a.id = b.tmsentry_id and a.periode_id = period and a.branch_id = branch
                 where workingday_id in (select id from hr_working_days where swap_in_out = True));


    update sb_tms_tmsentry_details
    set time_in = null
    where id in (select b.id
                 from hr_tmsentry_summary a
                          join sb_tms_tmsentry_details b
                               on a.id = b.tmsentry_id and a.periode_id = period and a.branch_id = branch
                 where workingday_id in (select id from hr_working_days where swap_in_out = True));


    update sb_tms_tmsentry_details
    set time_in = time_out
    where id in (select b.id
                 from hr_tmsentry_summary a
                          join sb_tms_tmsentry_details b
                               on a.id = b.tmsentry_id and a.periode_id = period and a.branch_id = branch
                 where workingday_id in (select id from hr_working_days where swap_in_out = True));


    update sb_tms_tmsentry_details
    set time_out = null
    where id in (select b.id
                 from hr_tmsentry_summary a
                          join sb_tms_tmsentry_details b
                               on a.id = b.tmsentry_id and a.periode_id = period and a.branch_id = branch
                 where workingday_id in (select id from hr_working_days where swap_in_out = True));


    update sb_tms_tmsentry_details ts
    set time_out = ss.aot4,
        date_out = (ts.details_date + INTERVAL '1 day')::date


    from (select (details_date - INTERVAL '1 day')::date as details_date, aot4, sb_tms_tmsentry_details.employee_id


          from sb_tms_tmsentry_details
          where workingday_id in (select id from hr_working_days where swap_in_out = True)
            and aot4 is not null) ss,


         hr_tmsentry_summary a
    where a.id = ts.tmsentry_id
      and a.periode_id = period
      and a.branch_id = branch


      and ss.details_date = ts.details_date
      and ts.employee_id = ss.employee_id;


    update sb_tms_tmsentry_details
    set aot4 = null
    where id in (select b.id
                 from hr_tmsentry_summary a
                          join sb_tms_tmsentry_details b
                               on a.id = b.tmsentry_id and a.periode_id = period and a.branch_id = branch
                 where workingday_id in (select id from hr_working_days where swap_in_out = True));


--update hr_tms_summary from temp

    with temp_hts as (select employee_id,

                             area_id,

                             branch_id,

                             periode_id,

                             completed_hrd,

                             completed_ca,

                             task_hrd,

                             task_ca

                      from temp_hr_tmsentry_summary)

    update hr_tmsentry_summary hts

    set task_ca       = th.task_ca,
        task_hrd      = th.task_hrd,
        completed_ca  = th.completed_ca,
        completed_hrd = th.completed_hrd

    from temp_hts th

    where hts.employee_id = th.employee_id

      and hts.area_id = th.area_id

      and hts.branch_id = th.branch_id

      and hts.periode_id = th.periode_id;


--update sb_tms_tmsentry_details edited

    WITH temp AS (SELECT distinct tsttd.employee_id,

                                  tsttd.workingday_id,

                                  tsttd.details_date,

                                  hts.branch_id,

                                  hts.area_id,

                                  hts.periode_id,

                                  tsttd.approved,

                                  tsttd.edited_time_in,

                                  tsttd.edited_time_out,

                                  tsttd.remark_edit_attn,

                                  tsttd.approved_by_ca,

                                  tsttd.is_edited,

                                  tsttd.date_in,

                                  tsttd.date_out,

                                  tsttd.status

                  FROM temp_sb_tms_tmsentry_details tsttd

                           JOIN
                       temp_hr_tmsentry_summary thts ON tsttd.tmsentry_id = thts.id

                           JOIN
                       hr_tmsentry_summary hts ON thts.employee_id = hts.employee_id
                           AND thts.branch_id = hts.branch_id
                           AND thts.area_id = hts.area_id
                           AND thts.periode_id = hts.periode_id

                           JOIN
                       sb_tms_tmsentry_details sttd ON sttd.employee_id = tsttd.employee_id
                           AND sttd.details_date = tsttd.details_date)

    update sb_tms_tmsentry_details sttd

    set approved         = t.approved,

        edited_time_in   = t.edited_time_in,

        edited_time_out  = t.edited_time_out,

        remark_edit_attn = t.remark_edit_attn,

        approved_by_ca   = t.approved_by_ca,

        is_edited        = t.is_edited,

        date_in          = t.date_in,

        date_out         = t.date_out,

        status           = t.status

    from temp t,

         hr_tmsentry_summary hts

    where sttd.employee_id = t.employee_id

      and sttd.details_date = t.details_date

      and sttd.tmsentry_id = hts.id

      and hts.branch_id = t.branch_id

      and hts.area_id = t.area_id

      and hts.periode_id = t.periode_id;


-- insert status attendance with attendee or absent

    WITH tmsentry_details AS (SELECT sttd2.id,

                                     sttd2.tmsentry_id,

                                     sttd2.employee_id,

                                     details_date,

                                     type,

                                     make_time(
                                             floor(schedule_time_in)::int, -- Hour part

                                             round((schedule_time_in - floor(schedule_time_in)) * 60)::int, -- Minute part

                                             0::int -- Second part (set to 0)

                                     )       AS schd_in,

                                     make_time(
                                             floor(COALESCE(sttd2.edited_time_in, sttd2.time_in))::int, -- Hour part

                                             round((COALESCE(sttd2.edited_time_in, sttd2.time_in) -
                                                    floor(COALESCE(sttd2.edited_time_in, sttd2.time_in))) *
                                                   60)::int, -- Minute part

                                             0::int -- Second part (set to 0)

                                     )       AS time_in,

                                     make_time(
                                             floor(schedule_time_out)::int, -- Hour part

                                             round((schedule_time_out - floor(schedule_time_out)) * 60)::int, -- Minute part

                                             0::int -- Second part (set to 0)

                                     )       AS schd_out,

                                     make_time(
                                             floor(COALESCE(sttd2.edited_time_out, sttd2.time_out))::int, -- Hour part

                                             round((COALESCE(sttd2.edited_time_out, sttd2.time_out) -
                                                    floor(COALESCE(sttd2.edited_time_out, sttd2.time_out))) *
                                                   60)::int, -- Minute part

                                             0::int -- Second part (set to 0)

                                     )       AS time_out,

                                     CASE

                                         WHEN (coalesce(edited_time_in, time_in) > 0 /*!= 0 OR

coalesce(edited_time_in, time_in) IS NOT NULL*/) AND /*OR*/

                                              (coalesce(edited_time_out, time_out) > 0 /*!= 0 OR

coalesce(edited_time_out, time_out) IS NOT NULL*/) THEN 'Attendee'

                                         WHEN type = 'W' AND (time_in = 0 OR time_in IS NULL) AND
                                              (time_out = 0 OR time_out IS NULL) THEN 'Absent'

                                         WHEN type = 'W' AND ((time_in = 0 OR time_in IS NULL) OR
                                                              (time_out = 0 OR time_out IS NULL)) THEN 'Alpha 1/2'

                                         when type = 'W' and (coalesce(edited_time_out, time_out) < schedule_time_out)
                                             then 'jam pulang lebih awal'

                                         ELSE sttd2.status_attendance -- Default status in case no condition matches

                                         END AS status


                              /* -- perubahan case when untuk menambahkan status baru 'jam pulang lebih awal'

                              CASE

                              -- Tidak ada absen masuk & keluar

                              WHEN type = 'W'

                              AND (time_in IS NULL OR time_in = 0)

                              AND (time_out IS NULL OR time_out = 0)

                              THEN 'Absent'

                              -- Hanya salah satu yang kosong

                              WHEN type = 'W'

                              AND (time_in IS NULL OR time_in = 0

                              OR time_out IS NULL OR time_out = 0)

                              THEN 'Alpha 1/2'

                              -- Jam pulang lebih awal

                              WHEN type = 'W'

                              AND time_out < schedule_time_out and date_in=date_out

                              THEN 'Jam pulang lebih awal'

                              -- Kalau ada jam masuk dan keluar → Attendee

                              WHEN type = 'W'

                              AND time_in IS NOT NULL AND time_out IS NOT NULL

                              THEN 'Attendee'

                              -- Default fallback

                              ELSE sttd2.status_attendance

                              END AS status*/

-- EXTRACT(EPOCH FROM (

-- make_time(

-- floor(time_in)::int,

-- round((time_in - floor(time_in)) * 60)::int,

-- 0::int

-- ) - make_time(

-- floor(schedule_time_in)::int,

-- round((schedule_time_in - floor(schedule_time_in)) * 60)::int,

-- 0::int

-- )

-- )

-- ) / 60 AS delay -- Delay in minutes

/*CASE

WHEN sttd2.status_attendance = 'Half Day Leave' THEN 0

ELSE

coalesce(greatest(EXTRACT(EPOCH FROM (

make_time(

floor(time_in)::int,

round((time_in - floor(time_in)) * 60)::int,

0::int

) - (make_time(

floor(schedule_time_in)::int,

round((schedule_time_in - floor(schedule_time_in)) * 60)::int,

0::int

) + make_time(0::int, hwd.delay_allow::int, 0::int)::interval)

)

) / 60,0),0)

END AS delay*/ -- Delay in minutes with delay_allow and status_attendance != 'Half Day Leave'

                              FROM sb_tms_tmsentry_details sttd2

/*join hr_working_days hwd on hwd.id = sttd2.workingday_id*/),

         hts as (SELECT tmsentry_details.*,

                        hts.id AS summary_id,

                        hts.periode_id,

                        hts.area_id,

                        hts.branch_id

                 FROM tmsentry_details

                          JOIN hr_tmsentry_summary hts
                               ON hts.id = tmsentry_details.tmsentry_id)

    update sb_tms_tmsentry_details sttd

    set /*delay = hts.delay,*/

        status_attendance = hts.status

    from hts

    where sttd.id = hts.id

      and hts.periode_id = period

      and hts.area_id = l_area

      and hts.branch_id = branch;


    -- perubahan penambahan jam pulang yang kurang disini(mmk_jam_pulang_kurang)

-- update delay

/*with aa as (select hts.employee_id,

sttd.workingday_id,

hts.periode_id,

hts.area_id,

hts.branch_id,

sttd.details_date,

-- float_to_time(coalesce(sttd.edited_time_in, sttd.time_in)) as time_in,

make_time(

floor(coalesce(sttd.edited_time_in, sttd.time_in))::int, -- Hour part

round((coalesce(sttd.edited_time_in, sttd.time_in) - floor(coalesce(sttd.edited_time_in, sttd.time_in))) * 60)::int, -- Minute part

0::int) as time_in, -- Second part

-- float_to_time(coalesce(sttd.edited_time_out, sttd.time_out)) as time_out,

make_time(

floor(coalesce(sttd.edited_time_out, sttd.time_out))::int, -- Hour part

round((coalesce(sttd.edited_time_out, sttd.time_out) - floor(coalesce(sttd.edited_time_out, sttd.time_out))) * 60)::int, -- Minute part

0::int) as time_out,

sttd.status_attendance

from hr_tmsentry_summary hts

join sb_tms_tmsentry_details sttd on hts.id = sttd.tmsentry_id

where hts.periode_id = period

and hts.area_id = l_area

and hts.branch_id = branch),

bb as (select aa.*,

hwd.delay_allow,

-- float_to_time(hwd.fullday_from) as schd_in,

make_time(

floor(hwd.fullday_from)::int, -- Hour part

round((hwd.fullday_from - floor(hwd.fullday_from)) * 60)::int, -- Minute part

0::int) as schd_in, -- Second part

-- float_to_time(hwd.fullday_to) as schd_out,

make_time(

floor(hwd.fullday_to)::int, -- Hour part

round((hwd.fullday_to - floor(hwd.fullday_to)) * 60)::int, -- Minute part

0::int) as schd_out, -- Second part

-- float_to_time(hwd.fullday_from) + INTERVAL '1 minute' * hwd.delay_allow AS delay_tolerance

make_time(

floor(hwd.fullday_from)::int, -- Hour part

round((hwd.fullday_from - floor(hwd.fullday_from)) * 60)::int, -- Minute part

0::int) + INTERVAL '1 minute' * hwd.delay_allow AS delay_tolerance

from aa

join hr_working_days hwd on aa.workingday_id = hwd.id),

cc as (select bb.*,

case

when

bb.time_in > bb.schd_in

then case

-- when abs(trunc(

-- EXTRACT(EPOCH FROM (bb.delay_tolerance::time - bb.time_in::time)) /

-- 60)) < bb.delay_allow

-- then 0

when bb.time_in <= bb.delay_tolerance

then 0

else

abs(trunc(EXTRACT(EPOCH FROM (bb.time_in::time - bb.schd_in::time)) / 60)) end

else 0 end as delay

from bb)

-- select * from cc where cc.delay > 10;

update sb_tms_tmsentry_details s

set delay = cc.delay

from cc

where s.employee_id = cc.employee_id

and s.details_date = cc.details_date;


-- hitung delay level1 dan level 2

-- delay level1 adalah delay > 5 min dan < 10 min

-- delay level2 adalah delay > 10 min*/


-- mmk update terbaru update delay


    with aa as (select sttd.type,

                       hts.employee_id,

                       sttd.workingday_id,

                       hts.periode_id,

                       hts.area_id,

                       hts.branch_id,

                       sttd.details_date,

                       sttd.date_in,

                       sttd.date_out,

                       coalesce(sttd.edited_time_in, sttd.time_in)   as jam_masuk,

                       coalesce(sttd.edited_time_out, sttd.time_out) as jam_pulang,

                       schedule_time_out,

                       sttd.date_in::timestamp
                           + make_interval(
                               hours => floor(schedule_time_in)::int,
                               mins => round((schedule_time_in
                                   - floor(schedule_time_in)) * 60)::int
                             )                                       AS jadwal_masuk_full,

                       sttd.date_in::timestamp
                           + make_interval(
                               hours => floor(coalesce(sttd.edited_time_in, sttd.time_in))::int,
                               mins => round((coalesce(sttd.edited_time_in, sttd.time_in)
                                   - floor(coalesce(sttd.edited_time_in, sttd.time_in))) * 60)::int
                             )                                       AS jam_masuk_full,  -- actual jam masuk

                       sttd.date_out::timestamp
                           + make_interval(
                               hours => floor(schedule_time_out)::int,
                               mins => round((schedule_time_out
                                   - floor(schedule_time_out)) * 60)::int
                             )                                       AS jadwal_pulang_full,

                       sttd.date_out::timestamp
                           + make_interval(
                               hours => floor(coalesce(sttd.edited_time_out, sttd.time_out))::int,
                               mins => round((coalesce(sttd.edited_time_out, sttd.time_out)
                                   - floor(coalesce(sttd.edited_time_out, sttd.time_out))) * 60)::int
                             )                                       AS jam_pulang_full, -- actual jam pulang

                       make_time(
                               floor(coalesce(sttd.edited_time_in, sttd.time_in))::int, -- Hour part

                               round((coalesce(sttd.edited_time_in, sttd.time_in) -
                                      floor(coalesce(sttd.edited_time_in, sttd.time_in))) * 60)::int, -- Minute part

                               0::int)                               as time_in,         -- Second part

-- float_to_time(coalesce(sttd.edited_time_out, sttd.time_out)) as time_out,

                       make_time(
                               floor(coalesce(sttd.edited_time_out, sttd.time_out))::int, -- Hour part

                               round((coalesce(sttd.edited_time_out, sttd.time_out) -
                                      floor(coalesce(sttd.edited_time_out, sttd.time_out))) * 60)::int, -- Minute part

                               0::int)                               as time_out,

                       sttd.status_attendance

                from hr_tmsentry_summary hts

                         join sb_tms_tmsentry_details sttd on hts.id = sttd.tmsentry_id

                where hts.periode_id = period

                  and hts.area_id = l_area

                  and hts.branch_id = branch),

         bb as (select aa.*,

                       hwd.delay_allow,

-- float_to_time(hwd.fullday_from) as schd_in,

                       make_time(
                               floor(hwd.fullday_from)::int, -- Hour part

                               round((hwd.fullday_from - floor(hwd.fullday_from)) * 60)::int, -- Minute part

                               0::int)                                         as schd_in,  -- Second part

-- float_to_time(hwd.fullday_to) as schd_out,

                       make_time(
                               floor(hwd.fullday_to)::int, -- Hour part

                               round((hwd.fullday_to - floor(hwd.fullday_to)) * 60)::int, -- Minute part

                               0::int)                                         as schd_out, -- Second part

-- float_to_time(hwd.fullday_from) + INTERVAL '1 minute' * hwd.delay_allow AS delay_tolerance

                       make_time(
                               floor(hwd.fullday_from)::int, -- Hour part

                               round((hwd.fullday_from - floor(hwd.fullday_from)) * 60)::int, -- Minute part

                               0::int) + INTERVAL '1 minute' * hwd.delay_allow AS delay_tolerance

                from aa

                         join hr_working_days hwd on aa.workingday_id = hwd.id),

         cc as (select bb.*,

                       case

                           when
                               EXTRACT(EPOCH FROM (bb.jam_masuk_full - bb.jadwal_masuk_full)) > 0
                               then case
                               -- when abs(trunc(

-- EXTRACT(EPOCH FROM (bb.delay_tolerance::time - bb.time_in::time)) /

-- 60)) < bb.delay_allow

-- then 0

                                        when bb.time_in <= bb.delay_tolerance
                                            then 0

                                        else
                                            abs(trunc(EXTRACT(EPOCH FROM (bb.time_in::time - bb.delay_tolerance::time)) / 60)) end

                           else 0 end as delay,


--case when branch_id=1 then

                       case
                           when EXTRACT(EPOCH FROM (jam_pulang_full - jadwal_pulang_full)) < 0 then
                               abs((trunc(EXTRACT(EPOCH FROM (jadwal_pulang_full - jam_pulang_full)) / 60) / 2)) --kalkulasi mendapatkan perhitungan setengah hari kerja

                           else
                               0
                           end        as pinalty_absen_pulang_kurang,

--else

-- 0

--end as pinalty_absen_pulang_kurang, --- pinalty jika jam pulang pulang < dari jadwal kurang


--case when branch_id=1 then

                       case
                           when EXTRACT(EPOCH FROM (jam_pulang_full - jadwal_pulang_full)) < 0 then
                               'Jam pulang lebih awal' -- belum di fix kan apa nama status nya

                           else
                               null
                           end        as status_attendance_calculate

                --else

--null

--end as status_attendance_calculate -- status klo jam pulang < dari jadwal jam pulang

                from bb)

    update sb_tms_tmsentry_details s

    set delay            = cc.delay,

--set delay = cc.delay+cc.pinalty_absen_pulang_kurang, -- alternatif jika pinalty nya akan digabungkan ke delay lalu akan di hitung oleh deduction

        status_attendance=case
                              when cc.status_attendance_calculate is null then
                                  s.status_attendance

                              else
                                  cc.status_attendance_calculate
            end

    from cc

    where s.employee_id = cc.employee_id

      and s.details_date = cc.details_date;


    -- mmk akhir update terbaru delay

-- read permission ** kemungkian error logic terjadi disini karena jika karyawan terlambat trus ipc maka delay nya akan berubah menjadi 0 (butuh konfrimasi pic)

-- WITH permission_dates AS (SELECT he.name,

-- hpe.employee_id,

-- hlt.name ->> 'en_US' AS leave_type,

-- generate_series(hpe.permission_date_from::date, hpe."permission_date_To"::date,

-- interval '1 day')::date AS permission_date

-- FROM hr_permission_entry hpe

-- JOIN hr_employee he ON hpe.employee_id = he.id

-- JOIN hr_leave_type hlt ON hpe.holiday_status_id = hlt.id

-- WHERE hpe.area_id = l_area

-- AND hpe.branch_id = branch

-- AND hpe.permission_status = 'approved'),

-- flag as (SELECT pd.*,

-- hts.area_id,

-- hts.branch_id,

-- hts.periode_id

-- FROM permission_dates pd

-- JOIN hr_opening_closing hoc ON hoc.id = period

-- JOIN hr_tmsentry_summary hts ON hts.periode_id = hoc.id

-- AND hts.area_id = l_area

-- AND hts.branch_id = branch

-- AND hts.employee_id = pd.employee_id

-- WHERE pd.permission_date BETWEEN hoc.open_periode_from AND hoc.open_periode_to)


--read permission update 18/09/2025

    WITH permission_dates AS (SELECT he.name,

                                     hpe.employee_id,

                                     slm.code || '-' || slm.name             AS leave_type,

                                     generate_series(hpe.permission_date_from::date, hpe."permission_date_To"::date,
                                                     interval '1 day')::date AS permission_date

                              FROM hr_permission_entry hpe

                                       JOIN hr_employee he ON hpe.employee_id = he.id

--JOIN hr_leave_type hlt ON hpe.holiday_status_id = hlt.id --tidak terpakai karna ganti ke hpe.permission_type_id

                                       join sb_leave_benefit slb on hpe.permission_type_id = slb.id

                                       join sb_leave_master slm on slb.leave_master_id = slm.id

                              WHERE hpe.area_id = l_area

                                AND hpe.branch_id = branch

                                and hpe.permission_status = 'approved'),

         flag as (SELECT pd.*,

                         hts.area_id,

                         hts.branch_id,

                         hts.periode_id

                  FROM permission_dates pd

                           JOIN hr_opening_closing hoc ON hoc.id = period

                           JOIN hr_tmsentry_summary hts ON hts.periode_id = hoc.id
                      AND hts.area_id = l_area
                      AND hts.branch_id = branch
                      AND hts.employee_id = pd.employee_id

                  WHERE pd.permission_date BETWEEN hoc.open_periode_from AND hoc.open_periode_to)


    update sb_tms_tmsentry_details sttd

    set status_attendance = flag.leave_type,
        delay             = 0

    from flag,

         hr_tmsentry_summary hts2

    where sttd.details_date::date = flag.permission_date::date

      and sttd.employee_id = flag.employee_id

      and hts2.periode_id = period

      and hts2.area_id = l_area

      and hts2.branch_id = branch;


-- update delay status attendance half day leave dan delay in = 0

    update sb_tms_tmsentry_details s

    set delay = 0

    from hr_tmsentry_summary hts

    -- asal kondisi

--where (s.status_attendance LIKE '%Half Day Leave%' OR s.status_attendance LIKE '%Delay In%')

    where (lower(split_part(s.status_attendance, '-', 2)) LIKE '%ijin datang terlambat%' OR
           lower(split_part(s.status_attendance, '-', 2)) LIKE '%cuti setengah hari%')

      and hts.id = s.tmsentry_id

      and hts.periode_id = period

      and hts.area_id = l_area

      and hts.branch_id = branch;


    with aa as (select hts.employee_id,

                       hts.periode_id,

                       hts.area_id,

                       hts.branch_id,

                       sttd.details_date,

                       float_to_time(coalesce(sttd.edited_time_in, sttd.time_in))   as time_in,

                       float_to_time(coalesce(sttd.edited_time_out, sttd.time_out)) as time_out,

                       sttd.delay

                from hr_tmsentry_summary hts

                         join sb_tms_tmsentry_details sttd on hts.id = sttd.tmsentry_id

                where hts.periode_id = period

                  and hts.area_id = l_area

                  and hts.branch_id = branch

/*and hts.employee_id = 48067*/),

         bb as (select aa.*,

                       case when aa.delay > 10 then 1 end                   as delay_level2,

                       case when aa.delay > 0 and aa.delay <= 10 then 1 end as delay_level1

                from aa)

    update sb_tms_tmsentry_details s

    set delay_level1 = bb.delay_level1,

        delay_level2 = bb.delay_level2

    from bb

    where s.employee_id = bb.employee_id

      and s.details_date = bb.details_date;


-- tes update aof aot

    WITH flag AS (SELECT hoe.employee_id,

                         hoe.verify_time_from,

                         hoe.verify_time_to,

                         hoe.plann_date_from,

                         hoe.plann_date_to

                  FROM hr_overtime_employees hoe

                           JOIN hr_overtime_planning hop on hoe.planning_id = hop.id

                           JOIN hr_employee he on hoe.employee_id = he.id

                  WHERE he.allowance_ot = true

                    AND hop.state = 'approved'

                    AND hop.branch_id = branch

                    AND hop.area_id = l_area
--
--                    AND hop.approve1 = true
--
--                    AND hop.approve2 = true
--
--                    AND hop.approve3 = true

                    AND (is_cancel = false or is_cancel is null))

    UPDATE sb_tms_tmsentry_details sttd

    SET approval_ot_from = f.verify_time_from,

        approval_ot_to   = f.verify_time_to,

        plann_date_from  = f.plann_date_from,

        plann_date_to    = f.plann_date_to

    FROM hr_tmsentry_summary hts,

         flag f

    WHERE f.employee_id = hts.employee_id

      AND hts.id = sttd.tmsentry_id

      AND sttd.details_date = f.plann_date_from;

    -- AND ((f.plann_date_to > f.plann_date_from AND sttd.date_out <= f.plann_date_to) OR (f.plann_date_to = f.plann_date_from AND (sttd.date_out > sttd.date_in OR sttd.date_out = sttd.date_in)))

-- AND NOT (f.plann_date_to - f.plann_date_from = 1 AND sttd.date_in = f.plann_date_to AND sttd.date_out = f.plann_date_to);

-- AND ((sttd.date_in BETWEEN f.plann_date_from AND f.plann_date_to) OR (sttd.date_out BETWEEN f.plann_date_from AND f.plann_date_to));

-- AND (sttd.date_in BETWEEN f.plann_date_from AND f.plann_date_to)

-- AND (sttd.date_out BETWEEN f.plann_date_from AND f.plann_date_to);

-- AND sttd.date_in = f.plann_date_from

-- AND sttd.date_out = f.plann_date_to;


--update data longshift

    with xx as (

--row atas

        select he."name",

               sttd.employee_id,

               sttd.workingday_id,

               hwd.code workingday,

               sttd.details_date,

               sttd.date_in,

               sttd.date_out,

               sttd.schedule_time_in,

               sttd.schedule_time_out,

               sttd.time_in,

               sttd.time_out,

               sttd.approval_ot_from,

               sttd.approval_ot_to

        from sb_tms_tmsentry_details sttd

                 join sb_tms_tmsentry_details sttd2 on sttd.employee_id = sttd2.employee_id

                 join hr_employee he on sttd.employee_id = he.id

                 left join hr_working_days hwd on sttd.workingday_id = hwd.id

        where sttd.time_out = sttd2.time_out

          and (sttd2.time_in is null or sttd2.time_in = 0)

          and sttd2.details_date = sttd.details_date + interval '1 day'

          and sttd.date_out > sttd.date_in

        order by he."name"),

         yy as (

--row bawah

             select he."name",

                    sttd2.employee_id,

                    sttd2.workingday_id,

                    hwd.code workingday,

                    sttd2.details_date,

                    sttd2.date_in,

                    sttd2.date_out,

                    sttd2.schedule_time_in,

                    sttd2.schedule_time_out,

                    sttd2.time_in,

                    sttd2.time_out,

                    sttd2.approval_ot_from,

                    sttd2.approval_ot_to

             from sb_tms_tmsentry_details sttd

                      join sb_tms_tmsentry_details sttd2 on sttd.employee_id = sttd2.employee_id

                      join hr_employee he on sttd2.employee_id = he.id

                      left join hr_working_days hwd on sttd2.workingday_id = hwd.id

             where sttd.time_out = sttd2.time_out

               and (sttd2.time_in is null or sttd2.time_in = 0)

               and sttd2.details_date = sttd.details_date + interval '1 day'

               and sttd.date_out > sttd.date_in

             order by he."name"),

         zz as (select distinct he."name",

                                sttd.employee_id,

                                sttd.workingday_id,

                                sttd.details_date,

                                sttd.date_in,

                                sttd.date_out,

                                sttd.schedule_time_in,

                                sttd.schedule_time_out,

-- sttd.time_in,

-- sttd.time_out,

                                case

                                    when sttd.workingday_id is not null and sttd.employee_id = xx.employee_id and
                                         sttd.details_date = xx.details_date then xx.schedule_time_out

                                    when sttd.workingday_id is null and sttd.employee_id = xx.employee_id and
                                         sttd.details_date = xx.details_date then xx.approval_ot_to

                                    else sttd.time_out
                                    end as time_out,

                                case

                                    when sttd.workingday_id is not null and sttd.employee_id = yy.employee_id and
                                         sttd.details_date = yy.details_date then yy.schedule_time_in

                                    when sttd.workingday_id is null and sttd.employee_id = yy.employee_id and
                                         sttd.details_date = yy.details_date then yy.approval_ot_from

                                    else sttd.time_in
                                    end as time_in,

                                sttd.approval_ot_from,

                                sttd.approval_ot_to

                from sb_tms_tmsentry_details sttd

                         join xx on sttd.employee_id = xx.employee_id

                         join yy on sttd.employee_id = yy.employee_id

                         join hr_employee he on sttd.employee_id = he.id

                where sttd.employee_id in (xx.employee_id, yy.employee_id)
                  and sttd.details_date in (xx.details_date, yy.details_date))

    update sb_tms_tmsentry_details sttd

    set time_in           = zz.time_in,
        time_out          = zz.time_out,
        date_in           = sttd.details_date,
        remark_edit_attn  = 'update long shift',
        status_attendance = 'Attendee'

    from zz

    where sttd.employee_id = zz.employee_id
      and sttd.details_date = zz.details_date;


    -- --tes new update aot1

-- update sb_tms_tmsentry_details sttd

-- set aot1 =

-- /*case

-- when sttd.date_in = sttd.date_out then -- tidak pergantian hari

-- case

-- when sttd.time_in <= sttd.approval_ot_from and sttd.time_out >= sttd.approval_ot_to and (sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from) then FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2 --hos.aot_to - hos.aot_from::float

-- when sttd.time_in <= sttd.approval_ot_from and sttd.time_out < sttd.approval_ot_to and (sttd.time_out - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from) then FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2 --hos.aot_to - hos.aot_from::float

-- when sttd.time_in > sttd.approval_ot_from and sttd.time_out >= sttd.approval_ot_to and (sttd.approval_ot_to - sttd.time_in) >= (hos.aot_to - hos.aot_from) then FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2 --hos.aot_to - hos.aot_from::float

-- when sttd.time_in > sttd.approval_ot_from and sttd.time_out < sttd.approval_ot_to and (sttd.time_out - sttd.time_in) >= (hos.aot_to - hos.aot_from) then FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2 --hos.aot_to - hos.aot_from::float

-- else null

-- end

-- when sttd.date_in < sttd.date_out then -- pergantian hari

-- case

-- when sttd.time_in <= sttd.approval_ot_from and sttd.time_out + 24 > sttd.approval_ot_to and sttd.approval_ot_from < sttd.approval_ot_to and (sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from) then FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2 --hos.aot_to - hos.aot_from::float

-- when sttd.time_in <= sttd.approval_ot_from and sttd.time_out + 24 > sttd.approval_ot_to + 24 and sttd.approval_ot_from > sttd.approval_ot_to and (24 + sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from) then FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2 --hos.aot_to - hos.aot_from::float

-- when sttd.time_in <= sttd.approval_ot_from and sttd.time_out + 24 < sttd.approval_ot_to + 24 and sttd.approval_ot_from > sttd.approval_ot_to and (24 + sttd.time_out - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from) then FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2 --hos.aot_to - hos.aot_from::float

-- when sttd.time_in > sttd.approval_ot_from and sttd.time_out + 24 > sttd.approval_ot_to and sttd.approval_ot_from < sttd.approval_ot_to and (sttd.approval_ot_to - sttd.time_in) >= (hos.aot_to - hos.aot_from) then FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2 --hos.aot_to - hos.aot_from::float

-- when sttd.time_in > sttd.approval_ot_from and sttd.time_out + 24 > sttd.approval_ot_to + 24 and sttd.approval_ot_from > sttd.approval_ot_to and (24 + sttd.approval_ot_to - sttd.time_in) >= (hos.aot_to - hos.aot_from) then FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2 --hos.aot_to - hos.aot_from::float

-- when sttd.time_in > sttd.approval_ot_from and sttd.time_out + 24 < sttd.approval_ot_to + 24 and sttd.approval_ot_from > sttd.approval_ot_to and (24 + sttd.time_out - sttd.time_in) >= (hos.aot_to - hos.aot_from) then FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2 --hos.aot_to - hos.aot_from::float

-- else null

-- end

-- else null

-- end*/

-- CASE

-- WHEN sttd.date_in = sttd.date_out THEN

-- CASE

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) >= sttd.approval_ot_to AND

-- (sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from)

-- THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) < sttd.approval_ot_to AND

-- (COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) >=

-- (hos.aot_to - hos.aot_from) THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) >= sttd.approval_ot_to AND

-- (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) >=

-- (hos.aot_to - hos.aot_from) THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) < sttd.approval_ot_to AND

-- (COALESCE(sttd.edited_time_out, sttd.time_out) -

-- COALESCE(sttd.edited_time_in, sttd.time_in)) >= (hos.aot_to - hos.aot_from)

-- THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

-- ELSE NULL

-- END

-- WHEN sttd.date_in < sttd.date_out THEN

-- CASE

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND

-- sttd.approval_ot_from < sttd.approval_ot_to AND

-- (sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from)

-- THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from)

-- THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) >=

-- (hos.aot_to - hos.aot_from) THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND

-- sttd.approval_ot_from < sttd.approval_ot_to AND

-- (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) >=

-- (hos.aot_to - hos.aot_from) THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) >=

-- (hos.aot_to - hos.aot_from) THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + COALESCE(sttd.edited_time_out, sttd.time_out) -

-- COALESCE(sttd.edited_time_in, sttd.time_in)) >= (hos.aot_to - hos.aot_from)

-- THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

-- ELSE NULL

-- END

-- ELSE NULL

-- END

-- from hr_overtime_setting hos

-- where sttd.approval_ot_from notnull

-- and sttd.approval_ot_to notnull

-- and sttd.workingday_id notnull

-- and hos.name = 'AOT1'

-- and hos.type = 'reguler';

-- -- and (sttd.delay <= 0 or sttd.delay is null)


-- -- tes new update aot2

-- UPDATE sb_tms_tmsentry_details sttd

-- SET aot2 =

-- CASE

-- WHEN sttd.date_in = sttd.date_out THEN -- tidak pergantian hari

-- CASE

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) >= sttd.approval_ot_to AND

-- (sttd.approval_ot_to - sttd.approval_ot_from) > 1 AND

-- (sttd.approval_ot_to - sttd.approval_ot_from) < (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((sttd.approval_ot_to - (sttd.approval_ot_from + 1)::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) < sttd.approval_ot_to AND

-- (COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) > 1 AND

-- (COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) < (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((COALESCE(sttd.edited_time_out, sttd.time_out) - (sttd.approval_ot_from + 1)::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) >= sttd.approval_ot_to AND

-- (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) > 1 AND

-- (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) < (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((sttd.approval_ot_to - (COALESCE(sttd.edited_time_in, sttd.time_in) + 1)::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) < sttd.approval_ot_to AND

-- (COALESCE(sttd.edited_time_out, sttd.time_out) - COALESCE(sttd.edited_time_in, sttd.time_in)) > 1 AND

-- (COALESCE(sttd.edited_time_out, sttd.time_out) - COALESCE(sttd.edited_time_in, sttd.time_in)) < (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((COALESCE(sttd.edited_time_out, sttd.time_out) - (COALESCE(sttd.edited_time_in, sttd.time_in) + 1)::float) * 2) / 2, 0)

-- ELSE NULL

-- END

-- WHEN sttd.date_in < sttd.date_out THEN -- pergantian hari

-- CASE

-- -- durasi absen lebih dari durasi overtime setting OT 2

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND

-- sttd.approval_ot_from < sttd.approval_ot_to AND

-- (sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND

-- sttd.approval_ot_from < sttd.approval_ot_to AND

-- (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) >= (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) >= (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + COALESCE(sttd.edited_time_out, sttd.time_out) - COALESCE(sttd.edited_time_in, sttd.time_in)) >= (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

--

-- -- durasi absen kurang dari durasi overtime setting OT 2

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND

-- sttd.approval_ot_from < sttd.approval_ot_to AND

-- (sttd.approval_ot_to - sttd.approval_ot_from) < (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((sttd.approval_ot_to - (sttd.approval_ot_from + 1)::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + sttd.approval_ot_to - sttd.approval_ot_from) < (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((24 + sttd.approval_ot_to - (sttd.approval_ot_from + 1)::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) < (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((24 + COALESCE(sttd.edited_time_out, sttd.time_out) - (sttd.approval_ot_from + 1)::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND

-- sttd.approval_ot_from < sttd.approval_ot_to AND

-- (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) < (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((sttd.approval_ot_to - (COALESCE(sttd.edited_time_in, sttd.time_in) + 1)::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) < (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((24 + sttd.approval_ot_to - (COALESCE(sttd.edited_time_in, sttd.time_in) + 1)::float) * 2) / 2, 0)

-- WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from AND

-- COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND

-- sttd.approval_ot_from > sttd.approval_ot_to AND

-- (24 + COALESCE(sttd.edited_time_out, sttd.time_out) - COALESCE(sttd.edited_time_in, sttd.time_in)) < (hos.aot_to - hos.aot_from) THEN

-- GREATEST(FLOOR((24 + COALESCE(sttd.edited_time_out, sttd.time_out) - (COALESCE(sttd.edited_time_in, sttd.time_in) + 1)::float) * 2) / 2, 0)

-- ELSE NULL

-- END

-- ELSE NULL

-- END

-- FROM hr_overtime_setting hos

-- WHERE sttd.approval_ot_from IS NOT NULL

-- AND sttd.approval_ot_to IS NOT NULL

-- AND sttd.workingday_id IS NOT NULL

-- AND hos.name = 'AOT2'

-- AND hos.type = 'reguler';

-- -- and (sttd.delay <= 0 or sttd.delay is null)

-- tes new update aot 1 dengan toleransi 5 menit (+ 0.08333)

    UPDATE sb_tms_tmsentry_details sttd

    SET aot1 =

            CASE

                WHEN coalesce(sttd.date_in, sttd.details_date) = coalesce(sttd.date_out, sttd.details_date) THEN
                    CASE

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= (sttd.approval_ot_from + 0.08333) AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) >= sttd.approval_ot_to AND
                             (sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from)
                            THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= (sttd.approval_ot_from + 0.08333) AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) < sttd.approval_ot_to AND
                             (COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) >=
                             (hos.aot_to - hos.aot_from) THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > (sttd.approval_ot_from + 0.08333) AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) >= sttd.approval_ot_to AND
                             (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) >=
                             (hos.aot_to - hos.aot_from) THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > (sttd.approval_ot_from + 0.08333) AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) < sttd.approval_ot_to AND
                             (COALESCE(sttd.edited_time_out, sttd.time_out) -
                              COALESCE(sttd.edited_time_in, sttd.time_in)) >= (hos.aot_to - hos.aot_from)
                            THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

                        ELSE NULL
                        END

                WHEN sttd.date_in < sttd.date_out THEN
                    CASE

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= (sttd.approval_ot_from + 0.08333) AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND
                             sttd.approval_ot_from < sttd.approval_ot_to AND
                             (sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from)
                            THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= (sttd.approval_ot_from + 0.08333) AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from)
                            THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= (sttd.approval_ot_from + 0.08333) AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) >=
                             (hos.aot_to - hos.aot_from) THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > (sttd.approval_ot_from + 0.08333) AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND
                             sttd.approval_ot_from < sttd.approval_ot_to AND
                             (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) >=
                             (hos.aot_to - hos.aot_from) THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > (sttd.approval_ot_from + 0.08333) AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) >=
                             (hos.aot_to - hos.aot_from) THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > (sttd.approval_ot_from + 0.08333) AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + COALESCE(sttd.edited_time_out, sttd.time_out) -
                              COALESCE(sttd.edited_time_in, sttd.time_in)) >= (hos.aot_to - hos.aot_from)
                            THEN FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2

                        ELSE NULL
                        END

                ELSE NULL
                END

    FROM hr_overtime_setting hos

    WHERE sttd.approval_ot_from IS NOT NULL

      AND sttd.approval_ot_to IS NOT NULL

      AND sttd.workingday_id IS NOT NULL

      AND hos.name = 'AOT1'

      AND hos.type = 'reguler';


-- tes new update aot 2 dengan toleransi 5 menit (+ 0.08333)

    UPDATE sb_tms_tmsentry_details sttd

    SET aot2 =

            CASE

                WHEN coalesce(sttd.date_in, sttd.details_date) = coalesce(sttd.date_out, sttd.details_date)
                    THEN -- tidak pergantian hari

                    CASE

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) >= sttd.approval_ot_to AND
                             (sttd.approval_ot_to - sttd.approval_ot_from) > 1 AND
                             (sttd.approval_ot_to - sttd.approval_ot_from) < (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((sttd.approval_ot_to - (sttd.approval_ot_from + 1)::float) * 2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) < sttd.approval_ot_to AND
                             (COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) > 1 AND
                             (COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) < (hos.aot_to - hos.aot_from)
                            THEN
                            GREATEST(FLOOR((COALESCE(sttd.edited_time_out, sttd.time_out) - (sttd.approval_ot_from + 1)::float) *
                                           2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) >= sttd.approval_ot_to AND
                             (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) > 1 AND
                             (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) < (hos.aot_to - hos.aot_from)
                            THEN
                            GREATEST(FLOOR((sttd.approval_ot_to - (COALESCE(sttd.edited_time_in, sttd.time_in) + 1)::float) * 2) /
                                     2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) < sttd.approval_ot_to AND
                             (COALESCE(sttd.edited_time_out, sttd.time_out) - COALESCE(sttd.edited_time_in, sttd.time_in)) > 1 AND
                             (COALESCE(sttd.edited_time_out, sttd.time_out) - COALESCE(sttd.edited_time_in, sttd.time_in)) <
                             (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((COALESCE(sttd.edited_time_out, sttd.time_out) -
                                            (COALESCE(sttd.edited_time_in, sttd.time_in) + 1)::float) * 2) / 2, 0)

                        ELSE NULL
                        END

                WHEN sttd.date_in < sttd.date_out THEN -- pergantian hari

                    CASE

-- durasi absen lebih dari durasi overtime setting OT 2

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND
                             sttd.approval_ot_from < sttd.approval_ot_to AND
                             (sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + sttd.approval_ot_to - sttd.approval_ot_from) >= (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) >=
                             (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND
                             sttd.approval_ot_from < sttd.approval_ot_to AND
                             (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) >= (hos.aot_to - hos.aot_from)
                            THEN
                            GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) >=
                             (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + COALESCE(sttd.edited_time_out, sttd.time_out) - COALESCE(sttd.edited_time_in, sttd.time_in)) >=
                             (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((hos.aot_to - hos.aot_from::float) * 2) / 2, 0)

-- durasi absen kurang dari durasi overtime setting OT 2

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND
                             sttd.approval_ot_from < sttd.approval_ot_to AND
                             (sttd.approval_ot_to - sttd.approval_ot_from) < (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((sttd.approval_ot_to - (sttd.approval_ot_from + 1)::float) * 2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + sttd.approval_ot_to - sttd.approval_ot_from) < (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((24 + sttd.approval_ot_to - (sttd.approval_ot_from + 1)::float) * 2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) <= sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + COALESCE(sttd.edited_time_out, sttd.time_out) - sttd.approval_ot_from) <
                             (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((24 + COALESCE(sttd.edited_time_out, sttd.time_out) -
                                            (sttd.approval_ot_from + 1)::float) * 2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to AND
                             sttd.approval_ot_from < sttd.approval_ot_to AND
                             (sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) < (hos.aot_to - hos.aot_from)
                            THEN
                            GREATEST(FLOOR((sttd.approval_ot_to - (COALESCE(sttd.edited_time_in, sttd.time_in) + 1)::float) * 2) /
                                     2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 > sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + sttd.approval_ot_to - COALESCE(sttd.edited_time_in, sttd.time_in)) <
                             (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((24 + sttd.approval_ot_to - (COALESCE(sttd.edited_time_in, sttd.time_in) + 1)::float) *
                                           2) / 2, 0)

                        WHEN COALESCE(sttd.edited_time_in, sttd.time_in) > sttd.approval_ot_from + 0.08333 AND
                             COALESCE(sttd.edited_time_out, sttd.time_out) + 24 < sttd.approval_ot_to + 24 AND
                             sttd.approval_ot_from > sttd.approval_ot_to AND
                             (24 + COALESCE(sttd.edited_time_out, sttd.time_out) - COALESCE(sttd.edited_time_in, sttd.time_in)) <
                             (hos.aot_to - hos.aot_from) THEN
                            GREATEST(FLOOR((24 + COALESCE(sttd.edited_time_out, sttd.time_out) -
                                            (COALESCE(sttd.edited_time_in, sttd.time_in) + 1)::float) * 2) / 2, 0)

                        ELSE NULL
                        END

                ELSE NULL
                END

    FROM hr_overtime_setting hos

    WHERE sttd.approval_ot_from IS NOT NULL

      AND sttd.approval_ot_to IS NOT NULL

      AND sttd.workingday_id IS NOT NULL

      AND hos.name = 'AOT2'

      AND hos.type = 'reguler';


-- update aot1 aot2 - delay

    with xx as (select employee_id,

                       details_date,

                       aot1,

                       aot2,

                       greatest(delay, 0) as delay,

                       case

                           when aot1 + aot2 - greatest((COALESCE(sttd.delay, 0)::float / 60), 0) >= 1 then 1

                           else FLOOR((greatest(aot1 + aot2 - greatest((COALESCE(sttd.delay, 0)::float / 60), 0), 0)) *
                                      2) / 2
                           end            as aot1_update,

                       case

                           when aot1 + aot2 - greatest((COALESCE(sttd.delay, 0)::float / 60), 0) > 1 then FLOOR(
                                   (GREATEST(aot1 + aot2 - GREATEST((COALESCE(sttd.delay, 0)::float / 60), 0) - 1, 0) *
                                    2) / 2)

                           else 0
                           end            as aot2_update

                from sb_tms_tmsentry_details sttd

                where aot1 is not null

                  and aot2 is not null

                  and sttd.workingday_id is not null

                  and delay > 0)

    update sb_tms_tmsentry_details sttd

    set aot1 = xx.aot1_update,

        aot2 = xx.aot2_update

    from xx

    where sttd.employee_id = xx.employee_id

      and sttd.details_date = xx.details_date

      and sttd.aot1 is not null

      and sttd.aot2 is not null

      and sttd.delay > 0

      and sttd.workingday_id is not null;


-- calculate OT holiday

    WITH date_series AS (SELECT aa.*,
                                CASE
                                    WHEN COALESCE(NULLIF(sttd.edited_time_in, 0), NULLIF(sttd.time_in, 0)) <
                                         aa.verify_time_from + 0.08333 --toleransi 5 menit
                                        THEN aa.verify_time_from
                                    ELSE COALESCE(NULLIF(sttd.edited_time_in, 0), NULLIF(sttd.time_in, 0))
                                    END AS ot_time_in,
                                CASE
                                    WHEN COALESCE(NULLIF(sttd.edited_time_out, 0), NULLIF(sttd.time_out, 0)) > aa.verify_time_to
                                        THEN aa.verify_time_to
                                    ELSE COALESCE(NULLIF(sttd.edited_time_out, 0), NULLIF(sttd.time_out, 0))
                                    END AS ot_time_out
                         FROM (SELECT hoe.employee_id,
                                      generate_series(hoe.plann_date_from::date, hoe.plann_date_to::date,
                                                      interval '1 day')::date AS ot_date,
                                      hoe.verify_time_from,
                                      hoe.verify_time_to
                               FROM hr_overtime_employees hoe
                               WHERE ot_type = 'holiday') aa
                                  JOIN sb_tms_tmsentry_details sttd
                                       ON aa.employee_id = sttd.employee_id
                                           AND aa.ot_date = sttd.details_date),

         first_ot AS (SELECT DISTINCT sttd.id           AS sttd_id,
                                      he.name,
                                      hoe.employee_id,
                                      hts.area_id,
                                      hts.branch_id,
                                      hts.periode_id,
                                      sttd.status_attendance,
                                      he.allowance_ot,
                                      hoe.ot_type,
                                      hop.state         AS ot_status,
                                      ds.ot_date,
                                      make_time(floor(ds.verify_time_from)::int,
                                                round((ds.verify_time_from - floor(ds.verify_time_from)) * 60)::int,
                                                0::int) AS ot_approve_from,

                                      make_time(floor(ds.verify_time_to)::int,
                                                round((ds.verify_time_to - floor(ds.verify_time_to)) * 60)::int,
                                                0::int) AS ot_approve_to,

                                      ds.ot_time_in     AS actual_timein,
                                      ds.ot_time_out    AS actual_timeout

                      FROM hr_overtime_planning hop
                               JOIN hr_overtime_employees hoe ON hop.id = hoe.planning_id
                               JOIN hr_employee he ON hoe.employee_id = he.id
                               JOIN hr_tmsentry_summary hts ON he.id = hts.employee_id
                               JOIN date_series ds ON hoe.employee_id = ds.employee_id
                               LEFT JOIN sb_tms_tmsentry_details sttd
                                         ON sttd.details_date = ds.ot_date
                                             AND sttd.employee_id = hoe.employee_id

                      WHERE hoe.ot_type = 'holiday'
                        AND hop.state = 'approved'
                        AND status_attendance = 'Attendee'

-- AND hts.employee_id = 48051

                        AND he.allowance_ot IS TRUE
                        AND hts.periode_id = period
                        AND hts.area_id = l_area
                        AND hts.branch_id = branch),


         second_ot AS (SELECT sttd_id,
                              name,
                              employee_id,
                              area_id,
                              branch_id,
                              periode_id,
                              allowance_ot,
                              status_attendance,
                              ot_type,
                              ot_status,
                              ot_date,
                              ot_approve_from,
                              ot_approve_to,
                              make_time(floor(first_ot.actual_timein)::int,
                                        round((first_ot.actual_timein - floor(first_ot.actual_timein)) * 60)::int,
                                        0::int) AS actual_timein,

                              make_time(floor(first_ot.actual_timeout)::int,
                                        round((first_ot.actual_timeout - floor(first_ot.actual_timeout)) * 60)::int,
                                        0::int) AS actual_timeout

                       FROM first_ot),

         third_ot AS (SELECT sttd_id,
                             name,
                             employee_id,
                             area_id,
                             branch_id,
                             periode_id,
                             allowance_ot,
                             status_attendance,
                             ot_type,
                             ot_status,
                             ot_date,
                             CASE
                                 WHEN actual_timein < ot_approve_from THEN ot_approve_from
                                 ELSE actual_timein
                                 END AS start_ot,

                             CASE
                                 WHEN actual_timeout > ot_approve_to THEN ot_approve_to
                                 ELSE actual_timeout
                                 END AS end_ot

                      FROM second_ot),

         fourth_ot AS (SELECT sttd_id,
                              name,
                              employee_id,
                              area_id,
                              branch_id,
                              periode_id,
                              allowance_ot,
                              status_attendance,
                              ot_type,
                              ot_status,
                              ot_date,
                              start_ot,
                              end_ot,
                              EXTRACT(HOUR FROM age(
                                      CASE
                                          WHEN start_ot > end_ot THEN (ot_date + interval '1 day')::date
                                          ELSE ot_date
                                          END +
                                      make_time(EXTRACT(HOUR FROM end_ot)::int, EXTRACT(MINUTE FROM end_ot)::int,
                                                0::int),
                                      ot_date +
                                      make_time(EXTRACT(HOUR FROM start_ot)::int, EXTRACT(MINUTE FROM start_ot)::int,
                                                0::int)
                                                ))   AS total_work_in_hour,

                              EXTRACT(MINUTE FROM age(
                                      CASE
                                          WHEN start_ot > end_ot THEN (ot_date + interval '1 day')::date
                                          ELSE ot_date
                                          END +
                                      make_time(EXTRACT(HOUR FROM end_ot)::int, EXTRACT(MINUTE FROM end_ot)::int,
                                                0::int),
                                      ot_date +
                                      make_time(EXTRACT(HOUR FROM start_ot)::int, EXTRACT(MINUTE FROM start_ot)::int,
                                                0::int)
                                                  )) AS minutes_left

                       FROM third_ot),

         ot AS (SELECT sttd_id,
                       name,
                       employee_id,
                       area_id,
                       branch_id,
                       periode_id,
                       allowance_ot,
                       status_attendance,
                       ot_type,
                       ot_status,
                       ot_date,
                       start_ot,
                       end_ot,
                       CASE
                           WHEN total_work_in_hour BETWEEN 6 AND 11 THEN total_work_in_hour - 0 --1

                           WHEN total_work_in_hour BETWEEN 12 AND 17 THEN total_work_in_hour - 0 --2

                           ELSE total_work_in_hour
                           END AS total_work_in_hour,

                       minutes_left

                FROM fourth_ot),


-- select * from fourth_ot;

         list_jam_istirahat AS (SELECT hts.branch_id,
                                       hts.periode_id,
                                       hts.employee_id,
                                       sttd.id                                                                  AS sttd_id,
                                       sttd.date_in,
                                       sttd.date_out,
                                       sttd.time_in,
                                       sttd.time_out,
                                       ot.total_work_in_hour,
                                       ot.start_ot,
                                       ot.end_ot,
                                       ot.minutes_left,
                                       -- waktu mulai lembur
                                       sttd.date_in + (ot.start_ot || ' hour')::interval                        AS datetime_in,
                                       -- waktu akhir lembur (+1 hari jika end_ot < start_ot)
                                       CASE
                                           WHEN ot.end_ot < ot.start_ot
                                               THEN (sttd.date_out + INTERVAL '1 day') + (ot.end_ot || ' hour')::interval
                                           ELSE sttd.date_out + (ot.end_ot || ' hour')::interval
                                           END                                                                  AS datetime_out,
                                       -- ubah ke angka jam (contoh: 19:30 → 19.5)
                                       EXTRACT(HOUR FROM ot.start_ot) + EXTRACT(MINUTE FROM ot.start_ot) / 60.0 AS start_ot_num,
                                       EXTRACT(HOUR FROM ot.end_ot) + EXTRACT(MINUTE FROM ot.end_ot) / 60.0     AS end_ot_num
                                FROM hr_tmsentry_summary hts
                                         JOIN sb_tms_tmsentry_details sttd ON hts.id = sttd.tmsentry_id
                                         JOIN hr_overtime_employees ss
                                              ON hts.employee_id = ss.employee_id
                                                  AND sttd.details_date = ss.plann_date_from
                                                  AND ss.ot_type = 'holiday'
                                         LEFT JOIN ot ON ot.sttd_id = sttd.id
                                WHERE 1 = 1
                                  AND hts.branch_id = branch
                                  AND hts.periode_id = period),
         break_schedule AS (SELECT sbm.branch_id,
                                   sbm.break_from,
                                   sbm.break_to
                            FROM sb_break_master sbm),
         break_calc AS (SELECT o.*,
                               b.break_from,
                               b.break_to,
                               -- tentukan waktu break (pertimbangkan lintas hari)
                               CASE
                                   WHEN b.break_from >= o.start_ot_num
                                       THEN o.date_in + (b.break_from || ' hour')::interval
                                   ELSE (o.date_in + INTERVAL '1 day') + (b.break_from || ' hour')::interval
                                   END AS break_from_time,
                               CASE
                                   WHEN b.break_to < b.break_from
                                       THEN (o.date_in + INTERVAL '1 day') + (b.break_to || ' hour')::interval
                                   WHEN b.break_to >= o.start_ot_num
                                       THEN o.date_in + (b.break_to || ' hour')::interval
                                   ELSE (o.date_in + INTERVAL '1 day') + (b.break_to || ' hour')::interval
                                   END AS break_to_time
                        FROM list_jam_istirahat o
                                 JOIN break_schedule b ON b.branch_id = o.branch_id),
         final_calc AS (SELECT bc.*,
                               GREATEST(0,
                                        EXTRACT(EPOCH FROM (
                                            LEAST(bc.datetime_out, bc.break_to_time) -
                                            GREATEST(bc.datetime_in, bc.break_from_time)
                                            )) / 3600
                               ) AS break_duration_hours
                        FROM break_calc bc
                        WHERE bc.datetime_out > bc.break_from_time
                          AND bc.datetime_in < bc.break_to_time),
         result_total_break_hours as (SELECT branch_id,
                                             periode_id,
                                             employee_id,
                                             sttd_id                                          AS id,
                                             minutes_left,
                                             MIN(date_in)                                     AS date_in,
                                             start_ot,
                                             end_ot,
                                             time_in,
                                             time_out,
                                             MAX(date_out)                                    AS date_out,
                                             MIN(datetime_in)                                 AS datetime_in,
                                             MAX(datetime_out)                                AS datetime_out,
                                             total_work_in_hour,
                                             SUM(break_duration_hours)                        AS total_break_hours,
                                             (total_work_in_hour - SUM(break_duration_hours)) as total_work_in_hour_result

                                      FROM final_calc
                                      --where employee_id =19588
                                      GROUP BY branch_id, periode_id, employee_id, sttd_id, total_work_in_hour, start_ot, end_ot,
                                               minutes_left, time_in, time_out
                                      ORDER BY employee_id, sttd_id),


         last as (SELECT ot.*,

                         CASE

                             WHEN total_work_in_hour_result < (SELECT aot_to FROM hr_overtime_setting WHERE id = 3)
                                 THEN CASE

                                          WHEN minutes_left BETWEEN 30 AND 60
                                              THEN total_work_in_hour_result + 0.5 --pembulatan sisa waktu

                                          ELSE total_work_in_hour_result
                                 END

                             ELSE (SELECT aot_to FROM hr_overtime_setting WHERE id = 3)
                             END AS ot2,

                         CASE

                             WHEN total_work_in_hour_result >= (SELECT aot_from FROM hr_overtime_setting WHERE id = 4) THEN
                                 (SELECT aot_from FROM hr_overtime_setting WHERE id = 4) - total_work_in_hour_result + 1

                             ELSE CASE

                                      WHEN total_work_in_hour_result = (SELECT aot_to FROM hr_overtime_setting WHERE id = 3)
                                          THEN CASE WHEN minutes_left BETWEEN 30 AND 60 THEN 0.5 ELSE 0 END

                                      ELSE 0
                                 END
                             END AS ot3,

                         CASE

                             WHEN total_work_in_hour_result >= (SELECT aot_from FROM hr_overtime_setting WHERE id = 5)
                                 THEN CASE
                                          WHEN minutes_left BETWEEN 30 AND 60
                                              THEN total_work_in_hour_result -
                                                   (SELECT aot_to FROM hr_overtime_setting WHERE id = 3) - 1
                                          ELSE total_work_in_hour_result - (SELECT aot_to FROM hr_overtime_setting WHERE id = 3) -
                                               1
                                 END

                             ELSE 0
                             END AS ot4

                  FROM result_total_break_hours ot

                  WHERE ot.end_ot != '00:00:00'

                    AND ot.start_ot != '00:00:00')

    UPDATE sb_tms_tmsentry_details s

    SET aot2 = last.ot2,

        aot3 = last.ot3,

        aot4 = last.ot4

    FROM last

    WHERE s.id = last.id

      AND s.workingday_id IS NULL

      AND s.approval_ot_from notnull

      AND s.approval_ot_to notnull;


    /*--Potongan hitungan OT base on libur GH 20250917

    update sb_tms_tmsentry_details aa set aot2 = x.aot2

    from (

    select id,periode_id,branch_id,ist,aot2 from

    (select

    hts.periode_id,

    sttd.id,

    hts.branch_id,

    -- total jam istirahat yang benar-benar overlap

    (

    SELECT COALESCE(SUM(

    LEAST(sttd.time_out, sbm.break_to) - GREATEST(sttd.approval_ot_from, sbm.break_from)

    ), 0)

    FROM sb_break_master sbm

    WHERE sbm.branch_id = hts.branch_id

    -- hanya ambil break yang overlap dengan lembur

    AND sbm.break_to > sttd.approval_ot_from

    AND sbm.break_from < sttd.time_out

    ) AS ist,

    CASE

    WHEN sttd.time_out > sttd.approval_ot_from THEN

    GREATEST(

    sttd.aot2 - COALESCE((

    SELECT SUM(

    LEAST(sttd.time_out, sbm.break_to) - GREATEST(sttd.approval_ot_from, sbm.break_from)

    )

    FROM sb_break_master sbm

    WHERE sbm.branch_id = hts.branch_id

    AND sbm.break_to > sttd.approval_ot_from

    AND sbm.break_from < sttd.time_out

    ), 0),

    0

    )

    ELSE

    GREATEST(sttd.aot1, sttd.aot2)

    END AS aot2

    FROM sb_tms_tmsentry_details sttd

    JOIN hr_tmsentry_summary hts

    ON hts.id = sttd.tmsentry_id

    join hr_overtime_employees ss on hts.employee_id = ss.employee_id and sttd.details_date = ss.plann_date_from and ss.ot_type = 'holiday'

    WHERE aot2 is not null and hts.branch_id = branch AND hts.periode_id = period) xx where ist >= 0.5 )x

    where x.id = aa.id;*/


--POTONGAN HITUNGAN OT BASE ON LIBUR GH 20250917 v-1

    WITH list_jam_istirahat AS (SELECT DISTINCT hts.branch_id,

                                                hts.periode_id,

                                                hts.employee_id,

                                                sttd.id,

                                                sttd.date_in,

                                                sttd.date_out,

                                                sttd.time_in,

                                                sttd.time_out,

                                                sttd.date_in + (sttd.time_in || ' hour')::interval   AS datetime_in,

                                                sttd.date_out + (sttd.time_out || ' hour')::interval AS datetime_out,

                                                CASE

                                                    WHEN sbm.break_from = 0 THEN sttd.date_out + (sbm.break_from || ' hour')::interval

                                                    ELSE sttd.date_in + (sbm.break_from || ' hour')::interval
                                                    END                                              AS break_from,

                                                CASE

                                                    WHEN sbm.break_from = 0 THEN sttd.date_out + (sbm.break_to || ' hour')::interval

                                                    WHEN sbm.break_to < sbm.break_from
                                                        THEN sttd.date_out + (sbm.break_to || ' hour')::interval

                                                    ELSE sttd.date_in + (sbm.break_to || ' hour')::interval
                                                    END                                              AS break_to

                                FROM sb_break_master sbm

                                         JOIN hr_tmsentry_summary hts ON hts.branch_id = sbm.branch_id

                                         JOIN sb_tms_tmsentry_details sttd ON hts.id = sttd.tmsentry_id

                                         JOIN HR_OVERTIME_EMPLOYEES SS
                                              ON hts.EMPLOYEE_ID = SS.EMPLOYEE_ID AND STTD.DETAILS_DATE = SS.PLANN_DATE_FROM AND
                                                 SS.OT_TYPE = 'HOLIDAY'

                                where sttd.aot2 is not null
                                  AND HTS.BRANCH_ID = BRANCH
                                  AND HTS.PERIODE_ID = PERIOD)

    UPDATE SB_TMS_TMSENTRY_DETAILS AA
    SET AOT2 = X.calculated_ot2

    from (SELECT ist.id,

                 ist.periode_id,

                 ist.branch_id,

/* ist.date_in,

ist.date_out,

ist.time_in,

ist.time_out,

sttd.aot2,*/

                 sum(
                         EXTRACT(EPOCH FROM (ist.break_to::timestamp
                             - ist.break_from ::timestamp)) / 3600)  AS tot_jam_istirahat,

                 (sttd.aot2 - sum(
                         EXTRACT(EPOCH FROM (ist.break_to::timestamp
                             - ist.break_from ::timestamp)) / 3600)) AS calculated_ot2

          FROM list_jam_istirahat ist

                   JOIN sb_tms_tmsentry_details sttd ON sttd.id = ist.id

          WHERE ist.break_from BETWEEN ist.datetime_in AND ist.datetime_out

--AND sttd.date_in < sttd.date_out;

          group by ist.id,
                   ist.date_in,
                   ist.periode_id,
                   ist.date_out,
                   ist.time_in,
                   ist.time_out,
                   sttd.aot2,
                   ist.branch_id

          order by ist.id) x
    where x.tot_jam_istirahat >= 0.5

      and aa.id = x.id;


-- time allowance - premi holiday

    WITH tmsentry_data AS (SELECT sttd.id         as sttd_id,

                                  he.name,

                                  he.attende_premie,

                                  hts.employee_id,

                                  hts.periode_id,

                                  hts.area_id,

                                  hts.branch_id,

                                  sttd.details_date,

                                  sttd.date_in,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_in, sttd.time_in))::int,
                                          round((coalesce(sttd.edited_time_in, sttd.time_in) -
                                                 floor(coalesce(sttd.edited_time_in, sttd.time_in))) * 60)::int,
                                          0::int) AS time_in,

                                  sttd.date_out,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_out, sttd.time_out))::int,
                                          round((coalesce(sttd.edited_time_out, sttd.time_out) -
                                                 floor(coalesce(sttd.edited_time_out, sttd.time_out))) * 60)::int,
                                          0::int) AS time_out,

                                  sttd.aot2

                           FROM hr_tmsentry_summary hts

                                    JOIN sb_tms_tmsentry_details sttd ON hts.id = sttd.tmsentry_id

                                    JOIN hr_employee he ON hts.employee_id = he.id

                           WHERE /*hts.employee_id = 48072

AND*/ hts.periode_id = period

                             AND he.area = l_area

                             AND he.branch_id = branch

                             and he.attende_premie is true

                             and sttd.empgroup_id is null

                             and sttd.workingday_id is null

                             and sttd.status_attendance = 'Attendee'

                           order by sttd.details_date),

         cc as (select hop.state                                                               as status_ot,

                       hoe.employee_id,

                       hop.area_id,

                       hop.branch_id,

                       generate_series(plann_date_from, plann_date_to, interval '1 day')::date AS request_days

                from hr_overtime_planning hop

                         join hr_overtime_employees hoe on hop.id = hoe.planning_id

                where /*hoe.employee_id = 48072

and*/ hoe.ot_type = 'holiday'

                order by request_days),

         summary as (SELECT t.*,

                            sa.area_id,

                            sad.code,

                            make_time(
                                    floor(sad.time_from)::int,
                                    round((sad.time_from - floor(sad.time_from)) * 60)::int,
                                    0::int) AS sad_time_from,

                            make_time(
                                    floor(sad.time_to)::int,
                                    round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                    0::int) AS sad_time_to,

                            sad.qty         as premi_attendee

                     FROM sb_allowances sa

                              JOIN sb_allowance_details sad ON sa.id = sad.allowance_id

                              JOIN tmsentry_data t ON sa.area_id = t.area_id
                         AND t.time_in >= make_time(
                                 floor(sad.time_from)::int,
                                 round((sad.time_from - floor(sad.time_from)) * 60)::int,
                                 0::int)::time
                         AND t.time_out <= make_time(
                                 floor(sad.time_to)::int,
                                 round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                 0::int)::time

                     WHERE sa.area_id = l_area

                       AND sad.code = 'ashf'

                     ORDER BY t.details_date),

         ff as (select sttd_id,

                       name,

                       cc.status_ot,

                       cc.request_days,

                       s.employee_id,

                       s.periode_id,

                       s.branch_id,

                       s.details_date,

                       s.date_in,

                       s.time_in,

                       s.date_out,

                       s.time_out,

                       s.code,

                       s.sad_time_from,

                       s.sad_time_to,

                       CASE

                           WHEN aot2 >= 6 THEN 1

                           WHEN aot2 >= 4 AND aot2 < 6 THEN 0.5

                           WHEN aot2 < 4 THEN 0
                           END AS premi

                from summary s

                         join cc on s.employee_id = cc.employee_id and s.details_date = cc.request_days

                where (s.date_in != s.date_out or s.date_in = s.date_out))

    update sb_tms_tmsentry_details s

    set premi_attendee = ff.premi

    from ff

    where s.id = ff.sttd_id;


-- time allowance - premi regular

    WITH tmsentry_data AS (SELECT sttd.id         as sttd_id,

                                  he.name,

                                  he.attende_premie,

                                  hts.employee_id,

                                  hts.periode_id,

                                  hts.area_id,

                                  hts.branch_id,

                                  sttd.details_date,

                                  sttd.date_in,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_in, sttd.time_in))::int,
                                          round((coalesce(sttd.edited_time_in, sttd.time_in) -
                                                 floor(coalesce(sttd.edited_time_in, sttd.time_in))) * 60)::int,
                                          0::int) AS time_in,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_out, sttd.time_out))::int,
                                          round((coalesce(sttd.edited_time_out, sttd.time_out) -
                                                 floor(coalesce(sttd.edited_time_out, sttd.time_out))) * 60)::int,
                                          0::int) AS time_out

                           FROM hr_tmsentry_summary hts

                                    JOIN sb_tms_tmsentry_details sttd ON hts.id = sttd.tmsentry_id

                                    JOIN hr_employee he ON hts.employee_id = he.id

                           WHERE /*hts.employee_id = 48051

AND*/ hts.periode_id = period

                             AND he.area = l_area

                             AND he.branch_id = branch

                             and he.attende_premie is true

                             and he.attende_premie is true

                             and sttd.empgroup_id is not null

                             and sttd.workingday_id is not null

                             and sttd.status_attendance = 'Attendee'),

         summary as (SELECT t.*,

                            sa.area_id,

                            sad.code,

                            make_time(
                                    floor(sad.time_from)::int,
                                    round((sad.time_from - floor(sad.time_from)) * 60)::int,
                                    0::int) AS sad_time_from,

                            make_time(
                                    floor(sad.time_to)::int,
                                    round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                    0::int) AS sad_time_to,

                            sad.qty         as premi_attendee

                     FROM sb_allowances sa

                              JOIN sb_allowance_details sad ON sa.id = sad.allowance_id

                              JOIN tmsentry_data t ON sa.area_id = t.area_id
                         AND t.time_in >= make_time(
                                 floor(sad.time_from)::int,
                                 round((sad.time_from - floor(sad.time_from)) * 60)::int,
                                 0::int)::time
                         AND t.time_out <= make_time(
                                 floor(sad.time_to)::int,
                                 round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                 0::int)::time

                     WHERE sa.area_id = l_area

                       AND sad.code = 'ashf'

                     ORDER BY t.details_date)

    update sb_tms_tmsentry_details s

    set premi_attendee = summary.premi_attendee

    from summary

    where s.id = summary.sttd_id;


-- time allowance - ans1 regular

    WITH tmsentry_data AS (SELECT sttd.id         as sttd_id,

                                  he.name,

                                  he.allowance_night_shift,

                                  hts.employee_id,

                                  hts.periode_id,

                                  hts.area_id,

                                  hts.branch_id,

                                  sttd.details_date,

                                  sttd.date_in,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_in, sttd.time_in))::int,
                                          round((coalesce(sttd.edited_time_in, sttd.time_in) -
                                                 floor(coalesce(sttd.edited_time_in, sttd.time_in))) * 60)::int,
                                          0::int) AS time_in,

                                  sttd.date_out,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_out, sttd.time_out))::int,
                                          round((coalesce(sttd.edited_time_out, sttd.time_out) -
                                                 floor(coalesce(sttd.edited_time_out, sttd.time_out))) * 60)::int,
                                          0::int) AS time_out

                           FROM hr_tmsentry_summary hts

                                    JOIN sb_tms_tmsentry_details sttd ON hts.id = sttd.tmsentry_id

                                    join hr_working_days hwd on sttd.workingday_id = hwd.id --tambahan

                                    JOIN hr_employee he ON hts.employee_id = he.id

                           WHERE /*hts.employee_id = 48051

AND*/ hts.periode_id = period

                             AND he.area = l_area

                             AND he.branch_id = branch

                             and he.allowance_night_shift is true

                             and sttd.empgroup_id is not null

                             and sttd.workingday_id is not null

                             --  and hwd.type_hari = 'shift' --tambahan

                             and hwd.code like '%2%'), --tambahan

         summary as (SELECT t.*,

                            sa.area_id      as area,

                            sad.code,

                            make_time(
                                    floor(sad.time_from)::int,
                                    round((sad.time_from - floor(sad.time_from)) * 60)::int,
                                    0::int) AS sad_time_from,

                            make_time(
                                    floor(sad.time_to)::int,
                                    round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                    0::int) AS sad_time_to,

                            sad.qty         as night_shift

                     FROM sb_allowances sa

                              JOIN sb_allowance_details sad ON sa.id = sad.allowance_id

                              JOIN tmsentry_data t ON sa.area_id = t.area_id

                     WHERE sa.area_id = l_area

                       AND sad.code = 'ans1'

                       AND ((t.time_in <= make_time(
                             floor(sad.time_from)::int,
                             round((sad.time_from - floor(sad.time_from)) * 60)::int,
                             0::int)::time
                         AND t.time_out >= make_time(
                                 floor(sad.time_to)::int,
                                 round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                 0::int)::time /*OR time_out >= '21:00:00'*/)
                         OR (t.time_in <= make_time( --tambahan

                                 floor(sad.time_from)::int, --tambahan

                                 round((sad.time_from - floor(sad.time_from)) * 60)::int, --tambahan

                                 0::int)::time --tambahan

                             and t.time_out > '00:00:00' --tambahan

                             and t.date_out > t.date_in) --tambahan

                         )

                     ORDER BY t.details_date)

    update sb_tms_tmsentry_details s

    set night_shift = summary.night_shift

    from summary

    where s.id = summary.sttd_id;


-- time allowance - ans1 holiday

    WITH tmsentry_data AS (SELECT sttd.id         as sttd_id,

                                  he.name,

                                  he.allowance_night_shift,

                                  hts.employee_id,

                                  hts.periode_id,

                                  hts.area_id,

                                  hts.branch_id,

                                  sttd.details_date,

                                  sttd.date_in,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_in, sttd.time_in))::int,
                                          round((coalesce(sttd.edited_time_in, sttd.time_in) -
                                                 floor(coalesce(sttd.edited_time_in, sttd.time_in))) * 60)::int,
                                          0::int) AS time_in,

                                  sttd.date_out,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_out, sttd.time_out))::int,
                                          round((coalesce(sttd.edited_time_out, sttd.time_out) -
                                                 floor(coalesce(sttd.edited_time_out, sttd.time_out))) * 60)::int,
                                          0::int) AS time_out

                           FROM hr_tmsentry_summary hts

                                    JOIN sb_tms_tmsentry_details sttd ON hts.id = sttd.tmsentry_id

                                    JOIN hr_employee he ON hts.employee_id = he.id

                           WHERE /*hts.employee_id = 48066

AND*/ hts.periode_id = period

                             AND he.area = l_area

                             AND he.branch_id = branch

                             and he.allowance_night_shift is true

                             and sttd.date_in = sttd.date_out),

         cc as (select hop.state                                                               as status_ot,

                       hoe.employee_id,

                       hop.area_id,

                       hop.branch_id,

                       generate_series(plann_date_from, plann_date_to, interval '1 day')::date AS request_days

                from hr_overtime_planning hop

                         join hr_overtime_employees hoe on hop.id = hoe.planning_id

                where /*hoe.employee_id = 48066

and*/ hoe.ot_type = 'holiday'

                order by request_days),

         summary as (SELECT t.*,

                            sa.area_id      as area,

                            sad.code,

                            make_time(
                                    floor(sad.time_from)::int,
                                    round((sad.time_from - floor(sad.time_from)) * 60)::int,
                                    0::int) AS sad_time_from,

                            make_time(
                                    floor(sad.time_to)::int,
                                    round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                    0::int) AS sad_time_to,

                            sad.qty         as night_shift

                     FROM sb_allowances sa

                              JOIN sb_allowance_details sad ON sa.id = sad.allowance_id

                              JOIN tmsentry_data t ON sa.area_id = t.area_id

                     WHERE sa.area_id = l_area

                       AND sad.code = 'ans1'

                       AND (t.time_in <= make_time(
                             floor(sad.time_from)::int,
                             round((sad.time_from - floor(sad.time_from)) * 60)::int,
                             0::int)::time
                         AND t.time_out >= make_time(
                                 floor(sad.time_to)::int,
                                 round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                 0::int)::time /*OR time_out >= '21:00:00'*/)

                     ORDER BY t.details_date),

         ff as (select sttd_id,

                       name,

                       cc.status_ot,

                       cc.request_days,

                       s.allowance_night_shift,

                       s.employee_id,

                       s.periode_id,

                       s.area_id,

                       s.branch_id,

                       s.details_date,

                       s.date_in,

                       s.time_in,

                       s.date_out,

                       s.time_out,

                       s.code,

                       s.sad_time_from,

                       s.sad_time_to,

                       s.night_shift as premi_night_shift

                from summary s

                         join cc on s.employee_id = cc.employee_id and s.details_date = cc.request_days

                where s.date_in = s.date_out)

    update sb_tms_tmsentry_details s

    set night_shift = ff.premi_night_shift

    from ff

    where s.id = ff.sttd_id;


-- time allowance - ans2 regular

    WITH tmsentry_data AS (SELECT sttd.id         as sttd_id,

                                  he.name,

                                  he.allowance_night_shift,

                                  hts.employee_id,

                                  hts.periode_id,

                                  hts.area_id,

                                  hts.branch_id,

                                  sttd.details_date,

                                  sttd.date_in,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_in, sttd.time_in))::int,
                                          round((coalesce(sttd.edited_time_in, sttd.time_in) -
                                                 floor(coalesce(sttd.edited_time_in, sttd.time_in))) * 60)::int,
                                          0::int) AS time_in,

                                  sttd.date_out,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_out, sttd.time_out))::int,
                                          round((coalesce(sttd.edited_time_out, sttd.time_out) -
                                                 floor(coalesce(sttd.edited_time_out, sttd.time_out))) * 60)::int,
                                          0::int) AS time_out

                           FROM hr_tmsentry_summary hts

                                    JOIN sb_tms_tmsentry_details sttd ON hts.id = sttd.tmsentry_id

                                    join hr_working_days hwd on sttd.workingday_id = hwd.id --tambahan

                                    JOIN hr_employee he ON hts.employee_id = he.id

                           WHERE /*hts.employee_id = 48066

AND*/ hts.periode_id = period

                             AND he.area = l_area

                             AND he.branch_id = branch

                             and he.allowance_night_shift is true

                             and sttd.empgroup_id is not null

                             and sttd.workingday_id is not null

                             --and hwd.type_hari = 'shift' --tambahan

                             and hwd.code like '%3%' --tambahan

                             and sttd.date_in != sttd.date_out),

         summary as (SELECT t.*,

                            sa.area_id      as area,

                            sad.code,

                            make_time(
                                    floor(sad.time_from)::int,
                                    round((sad.time_from - floor(sad.time_from)) * 60)::int,
                                    0::int) AS sad_time_from,

                            make_time(
                                    floor(sad.time_to)::int,
                                    round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                    0::int) AS sad_time_to,

                            sad.qty         as night_shift

                     FROM sb_allowances sa

                              JOIN sb_allowance_details sad ON sa.id = sad.allowance_id

                              JOIN tmsentry_data t ON sa.area_id = t.area_id

                     WHERE sa.area_id = l_area

                       AND sad.code = 'ans2'

                       AND ((t.time_in <= make_time(
                             floor(sad.time_from)::int,
                             round((sad.time_from - floor(sad.time_from)) * 60)::int,
                             0::int)::time
                         OR
                             (t.date_in::DATE + t.time_in::TIME)::TIMESTAMP < (t.date_out::DATE + make_time(
                                     floor(sad.time_to)::int,
                                     round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                     0::int)::TIME)::TIMESTAMP)
                         AND t.time_out >= make_time(
                                 floor(sad.time_to)::int,
                                 round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                 0::int)::time /*OR time_out >= '02:00:00'*/)

                     ORDER BY t.details_date)

    update sb_tms_tmsentry_details s

    set night_shift2 = summary.night_shift

    from summary

    where s.id = summary.sttd_id;


-- time allowance - ans2 holiday

    WITH tmsentry_data AS (SELECT sttd.id         as sttd_id,

                                  he.name,

                                  he.allowance_night_shift,

                                  hts.employee_id,

                                  hts.periode_id,

                                  hts.area_id,

                                  hts.branch_id,

                                  sttd.details_date,

                                  sttd.date_in,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_in, sttd.time_in))::int,
                                          round((coalesce(sttd.edited_time_in, sttd.time_in) -
                                                 floor(coalesce(sttd.edited_time_in, sttd.time_in))) * 60)::int,
                                          0::int) AS time_in,

                                  sttd.date_out,

                                  make_time(
                                          floor(coalesce(sttd.edited_time_out, sttd.time_out))::int,
                                          round((coalesce(sttd.edited_time_out, sttd.time_out) -
                                                 floor(coalesce(sttd.edited_time_out, sttd.time_out))) * 60)::int,
                                          0::int) AS time_out

                           FROM hr_tmsentry_summary hts

                                    JOIN sb_tms_tmsentry_details sttd ON hts.id = sttd.tmsentry_id

                                    JOIN hr_employee he ON hts.employee_id = he.id

                           WHERE /*hts.employee_id = 48066

AND*/ hts.periode_id = period

                             AND he.area = l_area

                             AND he.branch_id = branch

                             and he.allowance_night_shift is true

                             and sttd.date_in != sttd.date_out)

-- select * from tmsentry_data;

            ,

         cc as (select hop.state                                                               as status_ot,

                       hoe.employee_id,

                       hop.area_id,

                       hop.branch_id,

                       generate_series(plann_date_from, plann_date_to, interval '1 day')::date AS request_days

                from hr_overtime_planning hop

                         join hr_overtime_employees hoe on hop.id = hoe.planning_id

                where /*hoe.employee_id = 48066

and*/ hoe.ot_type = 'holiday'

                order by request_days),

         summary as (SELECT t.*,

                            sa.area_id      as area,

                            sad.code,

                            make_time(
                                    floor(sad.time_from)::int,
                                    round((sad.time_from - floor(sad.time_from)) * 60)::int,
                                    0::int) AS sad_time_from,

                            make_time(
                                    floor(sad.time_to)::int,
                                    round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                    0::int) AS sad_time_to,

                            sad.qty         as night_shift

                     FROM sb_allowances sa

                              JOIN sb_allowance_details sad ON sa.id = sad.allowance_id

                              JOIN tmsentry_data t ON sa.area_id = t.area_id

                     WHERE sa.area_id = l_area

                       AND sad.code = 'ans2'

                       AND ((t.time_in <= make_time(
                             floor(sad.time_from)::int,
                             round((sad.time_from - floor(sad.time_from)) * 60)::int,
                             0::int)::time
                         OR
                             (t.date_in::DATE + t.time_in::TIME)::TIMESTAMP < (t.date_out::DATE + make_time(
                                     floor(sad.time_to)::int,
                                     round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                     0::int)::TIME)::TIMESTAMP)
                         AND t.time_out >= make_time(
                                 floor(sad.time_to)::int,
                                 round((sad.time_to - floor(sad.time_to)) * 60)::int,
                                 0::int)::time /*OR time_out >= '02:00:00'*/)

                     ORDER BY t.details_date),

         ff as (select sttd_id,

                       name,

                       cc.status_ot,

                       cc.request_days,

                       s.allowance_night_shift,

                       s.employee_id,

                       s.periode_id,

                       s.area_id,

                       s.branch_id,

                       s.details_date,

                       s.date_in,

                       s.time_in,

                       s.date_out,

                       s.time_out,

                       s.code,

                       s.sad_time_from,

                       s.sad_time_to,

                       s.night_shift as premi_night_shift

                from summary s

                         join cc on s.employee_id = cc.employee_id and s.details_date = cc.request_days

                where s.date_in != s.date_out)

    update sb_tms_tmsentry_details s

    set night_shift2 = ff.premi_night_shift

    from ff

    where s.id = ff.sttd_id;


    -- update delay status attendance half day leave = 0

-- update sb_tms_tmsentry_details s

-- set delay = 0

-- from hr_tmsentry_summary hts

-- where s.status_attendance like '%Half Day Leave%'

-- and hts.id = s.tmsentry_id

-- and hts.periode_id = period

-- and hts.area_id = l_area

-- and hts.branch_id = branch;


--update deduction 50 tambah case when 100

    with flag as (SELECT sttd.employee_id,

                         sttd.tmsentry_id,

                         COUNT(CASE WHEN sttd.delay > hwd.delay_allow THEN 1 END) AS count_delay,

                         SUM(sttd.delay)                                          AS sum_delay,

/* CASE

WHEN FLOOR(COUNT(CASE WHEN sttd.delay > hwd.delay_allow THEN 1 END) / 5) > FLOOR(SUM(sttd.delay) / 100) THEN FLOOR(COUNT(CASE WHEN sttd.delay > hwd.delay_allow THEN 1 END) / 6)

ELSE FLOOR(SUM(sttd.delay) / 100)

END AS total_deduction*/

                         case
                             when branch = 1 then
                                 CASE

                                     WHEN FLOOR(COUNT(CASE WHEN sttd.delay > hwd.delay_allow THEN 1 END) / 6) >
                                          FLOOR(SUM(sttd.delay) / 101)
                                         THEN FLOOR(COUNT(CASE WHEN sttd.delay > hwd.delay_allow THEN 1 END) / 6)

                                     ELSE FLOOR(SUM(sttd.delay) / 101)
                                     END

                             else
                                 CASE

                                     WHEN FLOOR(COUNT(CASE WHEN sttd.delay > 0 THEN 1 END) / 6) > FLOOR(SUM(sttd.delay) / 51)
                                         THEN FLOOR(COUNT(CASE WHEN sttd.delay > 0 THEN 1 END) / 6)

                                     ELSE count(sttd.delay)
                                     END
                             end                                                  as total_deduction

                  FROM sb_tms_tmsentry_details sttd

                           JOIN hr_working_days hwd ON sttd.workingday_id = hwd.id

                  WHERE sttd.delay > 0

                  GROUP BY sttd.employee_id, sttd.tmsentry_id)

    update hr_tmsentry_summary hts

    set is_deduction    =

            case

                when f.total_deduction > 0 then true

                else false
                end,

        total_deduction = f.total_deduction

    from flag f

    where f.tmsentry_id = hts.id

      and f.employee_id = hts.employee_id

      and hts.area_id = l_area

      and hts.branch_id = branch

      and hts.periode_id = period;


--update sheet atendee, permission, overtime, night shift dan absent

    with xx as (select sttd.employee_id,

                       sttd.workingday_id,

                       hwd.code,

                       sttd.details_date,

                       sttd.status_attendance,

                       sttd.approval_ot_from,

                       sttd.approval_ot_to,

                       sttd.details_date     as d_date,

                       TRIM(BOTH '.' FROM CONCAT(
                               CASE

                                   WHEN sttd.status_attendance = 'Attendee' THEN '10'

                                   ELSE ''
                                   END,
                               CASE

                                   WHEN sttd.status_attendance NOT IN
                                        ('Attendee', 'Absent', 'Alpha 1/2', 'Jam pulang lebih awal') AND
                                        sttd.status_attendance IS NOT NULL THEN '.20'

                                   ELSE ''
                                   END,
                               CASE

                                   WHEN sttd.aot1 IS NOT NULL OR sttd.aot2 IS NOT NULL THEN '.30'

                                   ELSE ''
                                   END,
                               CASE

                                   WHEN sttd.night_shift IS NOT NULL OR sttd.night_shift2 IS NOT NULL THEN '.40'

                                   ELSE ''
                                   END,
                               CASE

                                   WHEN sttd.status_attendance IN ('Absent', 'Jam pulang lebih awal', 'Alpha 1/2') THEN '.50'

                                   ELSE ''
                                   END
                                          )) AS flag

                from sb_tms_tmsentry_details sttd

                         left join hr_working_days hwd on sttd.workingday_id = hwd.id)

    update sb_tms_tmsentry_details sttd

    set flag = xx.flag

    from xx,
         hr_tmsentry_summary hts

    where sttd.employee_id = xx.employee_id

      and sttd.tmsentry_id = hts.id

      and sttd.details_date = xx.d_date

      and hts.periode_id = period

      and hts.area_id = l_area

      and hts.branch_id = branch;


--Realization form overtime GH 12 Nov 2025

    update hr_overtime_employees ho
    set realization_time_from      = xx.msk,
        realization_time_from_char = to_char(make_time(floor(xx.msk)::int, ((xx.msk - floor(xx.msk)) * 60)::int, 0), 'HH24:MI'),
        realization_time_to        = xx.klr,
        realization_time_to_char   = to_char(make_time(floor(xx.klr)::int, ((xx.klr - floor(xx.klr)) * 60)::int, 0), 'HH24:MI')
    from (select hts.employee_id,
                 sttd.details_date,
                 coalesce(sttd.edited_time_in, sttd.time_in)   msk,
                 coalesce(sttd.edited_time_out, sttd.time_out) klr
          from hr_tmsentry_summary hts,
               sb_tms_tmsentry_details sttd

          where hts.id = sttd.tmsentry_id
            and hts.branch_id = branch
            AND hts.periode_id = period) xx

    where ho.employee_id = xx.employee_id
      and xx.details_date = ho.plann_date_from;


--update total summary detail (footer) || code ini harus selalu paling bawah

    WITH flag AS (SELECT he.name,

                         he.employee_levels,

                         hts.employee_id,

                         hts.id                                                                    AS hts_id,

                         sum(case when type = 'W' then 1 else 0 end)                               AS total_workingday,

                         COUNT(CASE

                                   WHEN sttd.status_attendance = 'Attendee' THEN 1 END)            AS total_attendee,

                         COUNT(CASE WHEN sttd.status_attendance = 'Absent' THEN 1 END)             AS total_absent,

                         sum(case when left(sttd.status_attendance, 1) = 'S' then 1 else 0 end)    as total_sick,

                         SUM(CASE

                                 WHEN sttd.flag = '20' and left(sttd.status_attendance, 1) <> 'S' THEN 1

-- WHEN sttd.status_attendance = 'Half Day Leave - Cuti Setengah Hari' THEN 0.5

                                 ELSE 0
                             END)                                                                  AS total_leave,

                         SUM(COALESCE(sttd.delay_level2, 0)) + SUM(COALESCE(sttd.delay_level1, 0)) AS total_times_delayed,

                         SUM(sttd.delay)                                                           as delay_total,

                         SUM(sttd.aot1)                                                            AS aot1,

                         SUM(sttd.aot2)                                                            AS aot2,

                         SUM(sttd.aot3)                                                            AS aot3,

                         SUM(sttd.aot4)                                                            AS aot4,

                         SUM(sttd.premi_attendee)                                                  AS total_premi_attendee,

                         SUM(sttd.night_shift2)                                                    AS total_night_shift2,

                         SUM(sttd.transport)                                                       AS total_transport,

                         SUM(sttd.meal)                                                            AS total_meal,

                         SUM(sttd.night_shift)                                                     AS total_night_shift

                  FROM hr_tmsentry_summary hts

                           JOIN sb_tms_tmsentry_details sttd ON hts.id = sttd.tmsentry_id

                           JOIN hr_employee he ON hts.employee_id = he.id

                  WHERE /*hts.id = 146526

AND*/ hts.branch_id = branch

                    AND hts.area_id = l_area

                    AND hts.periode_id = period

                  GROUP BY he.name, hts.employee_id, hts.id, he.employee_levels)

    UPDATE hr_tmsentry_summary h

    SET attendee_total    = flag.total_workingday,

        attendee_count    = flag.total_attendee,

        absent_count      = flag.total_absent,

        leave_count       = flag.total_leave,

        ot1_totalx        = flag.aot1,

        ot2_totalx        = flag.aot2,

        ot3_totalx        = flag.aot3,

        ot4_totalx        = flag.aot4,

        delay_count       = flag.total_times_delayed,

        delay_total       = flag.delay_total,

        pattendace_count  = flag.total_premi_attendee,

        nightshift_count  = flag.total_night_shift,

        nightshift2_count = flag.total_night_shift2,

        transport_count   = flag.total_transport,

        meal_count        = flag.total_meal,

        sick_count        = flag.total_sick

    FROM flag

    WHERE h.id = flag.hts_id;
    -- and flag.employee_levels >= 6;


-- table monitoring

    DELETE FROM sb_incomplete_attendances WHERE period_id = period and area_id = l_area and branch_id = branch;

    DELETE FROM sb_incomplete_attendance_details WHERE period_id = period and area_id = l_area and branch_id = branch;


    DELETE FROM sb_attendance_corrections WHERE period_id = period and area_id = l_area and branch_id = branch;

    DELETE FROM sb_attendance_correction_details WHERE period_id = period and area_id = l_area and branch_id = branch;


-- master incomplete attendance

    insert into sb_incomplete_attendances as sia (period_id, area_id, branch_id, department_id)

    with aa as (select hts.periode_id,

                       hts.area_id,

                       hts.branch_id,

                       hts.department_id,

                       sttd.type,

                       sttd.details_date,

                       sttd.date_in,

                       coalesce(sttd.edited_time_in, sttd.time_in)   as time_in,

                       sttd.date_out,

                       coalesce(sttd.edited_time_out, sttd.time_out) as time_out,

                       sttd.status_attendance

                from hr_tmsentry_summary hts

                         join sb_tms_tmsentry_details sttd on hts.id = sttd.tmsentry_id

                where coalesce(sttd.edited_time_in, sttd.time_in) is null

                   or coalesce(sttd.edited_time_in, sttd.time_in) = 0

                   or coalesce(sttd.edited_time_out, sttd.time_out) is null

                   or coalesce(sttd.edited_time_out, sttd.time_out) = 0),

         bb as (select *

                from aa

                where aa.status_attendance not in ('Full Day Leave', 'Sick Leave', 'Unpaid Leave')

                  and aa.type = 'W'

                  and aa.periode_id = period

                  and aa.area_id = l_area

                  and aa.branch_id = branch)

    select bb.periode_id, bb.area_id, bb.branch_id, bb.department_id

    from bb

    group by bb.periode_id, bb.area_id, bb.branch_id, bb.department_id;


-- detail incomplete attendance

    delete

    from sb_incomplete_attendance_details siad

    where incomplete_attn_id in (select id

                                 from sb_incomplete_attendances sia

                                 where sia.period_id = period

                                   and sia.area_id = l_area

                                   and sia.branch_id = branch);


    delete

    from sb_incomplete_attendances sia

    where sia.period_id = period

      and sia.area_id = l_area

      and sia.branch_id = branch;


    insert into sb_incomplete_attendance_details as siad (incomplete_attn_id, period_id, type, area_id, branch_id, nik,
                                                          name,
                                                          department_id, job_id, wdcode, empgroup_id,
                                                          details_date, date_timein, time_in, date_timeout, time_out,
                                                          status_attendance)

    with aa as (select hts.periode_id,

                       sttd.type,

                       hts.area_id,

                       hts.branch_id,

                       he.nik,

                       he.name,

                       he.department_id,

                       he.job_id,

                       sttd.workingday_id,

                       sttd.empgroup_id,

                       sttd.details_date,

                       sttd.date_in,

                       coalesce(sttd.edited_time_in, time_in)        as time_in,

                       sttd.date_out,

                       coalesce(sttd.edited_time_out, sttd.time_out) as time_out,

                       sttd.status_attendance

                from hr_tmsentry_summary hts

                         join sb_tms_tmsentry_details sttd on hts.id = sttd.tmsentry_id

                         join hr_department hd on hts.department_id = hd.id

                         join hr_employee he on hts.employee_id = he.id

                where coalesce(sttd.edited_time_in, sttd.time_in) is null

                   or coalesce(sttd.edited_time_in, sttd.time_in) = 0

                   or coalesce(sttd.edited_time_out, sttd.time_out) is null

                   or coalesce(sttd.edited_time_out, sttd.time_out) = 0)

    select sia.id as incomplete_attn_id, aa.*

    from aa

             join sb_incomplete_attendances sia
                  on /*aa.periode_id = sia.period_id and aa.area_id = sia.area_id and aa.branch_id = sia.branch_id

and*/ aa.department_id = sia.department_id

    where aa.status_attendance not in ('Full Day Leave', 'Sick Leave', 'Unpaid Leave', 'Special Leave')

      and aa.periode_id = period

      and aa.area_id = l_area

      and aa.branch_id = branch

      and aa.type = 'W';


-- master koreksi absensi

    insert into sb_attendance_corrections as sac (period_id, branch_id, area_id, department_id)

    select hts.periode_id,

           he.branch_id,

           hts.area_id,

           he.department_id

    from hr_tmsentry_summary hts

             join sb_tms_tmsentry_details sttd on hts.id = sttd.tmsentry_id

             join hr_employee he on hts.employee_id = he.id

    where sttd.is_edited is true

      and hts.periode_id = period

      and hts.area_id = l_area

      and hts.branch_id = branch

    group by hts.periode_id, he.branch_id, hts.area_id, he.department_id;


-- monitoring kehadiran

    delete

    from sb_employee_attendance sea

    where sea.periode_id = period
      and sea.area_id = l_area
      and sea.branch_id = branch;


    insert into sb_employee_attendance(employee_id, area_id, branch_id, department_id, empgroup_id, nik,
                                       details_date, time_in, time_out, status_attendance, periode_id)

    select hts.employee_id,

           hts.area_id,

           hts.branch_id,

           hts.department_id,

           sttd.empgroup_id,

           he.nik,

           sttd.details_date                             as details_date,

           coalesce(sttd.edited_time_in, sttd.time_in)   as time_in,

           coalesce(sttd.edited_time_out, sttd.time_out) as time_out,

           sttd.status_attendance,

           hts.periode_id

    from hr_tmsentry_summary hts

             join sb_tms_tmsentry_details sttd on hts.id = sttd.tmsentry_id

             join hr_employee he on hts.employee_id = he.id

    where hts.periode_id = period

      and hts.area_id = l_area

      and hts.branch_id = branch

    order by sttd.details_date;


-- detail koreksi absensi

    insert into sb_attendance_correction_details as sacd (attn_correction_id, period_id, area_id,
                                                          branch_id, department_id, job_id, wdcode, empgroup_id,
                                                          nik, name, remark, tgl_time_in, tgl_time_out, time_in,
                                                          edited_time_in,
                                                          time_out, edited_time_out, delay)

    with aa as (select hts.periode_id,

                       hts.area_id,

                       he.branch_id,

                       he.department_id,

                       he.job_id,

                       sttd.workingday_id,

                       sttd.empgroup_id,

                       hts.nik,

                       he.name,

                       sttd.remark_edit_attn,

                       sttd.date_in,

                       sttd.date_out,

                       sttd.time_in,

                       sttd.edited_time_in,

                       sttd.time_out,

                       sttd.edited_time_out,

                       sttd.delay

                from hr_tmsentry_summary hts

                         join sb_tms_tmsentry_details sttd on hts.id = sttd.tmsentry_id

                         join hr_employee he on hts.employee_id = he.id

                where sttd.is_edited is true

                  and hts.periode_id = period

                  and hts.area_id = l_area

                  and hts.branch_id = branch)

    select sac.id, aa.*

    from aa

             join sb_attendance_corrections sac on aa.department_id = sac.department_id;


-- monitoring - request vs realization

    delete

    from sb_overtime_attendance soa

    where soa.periode_id = period

      and soa.area_id = l_area

      and soa.branch_id = branch;


    insert into sb_overtime_attendance as soa ( area_id, branch_id, department_id, periode_id, no_request
                                              , nik, req_date, employee_id, req_time_fr, req_time_to, rlz_time_fr
                                              , rlz_time_to, approve_time_from, approve_time_to, state, is_shuttle_car, is_dine_in
                                              , is_meal_cash, is_cancel, rlz_date, aot1, aot2, aot3, aot4, overtime)

    select hts.area_id,

           hts.branch_id,

           hts.department_id,

           hts.periode_id,

           hop.name                                      as no_request,

           hts.nik,

           hoe.plann_date_from                           as tgl_request,

           hts.employee_id,

           hoe.ot_plann_from                             as req_time_fr,

           hoe.ot_plann_to                               as req_time_to,

           coalesce(sttd.time_in, sttd.edited_time_in)   as rlz_time_fr,

           coalesce(sttd.time_out, sttd.edited_time_out) as rlz_time_to,

           sttd.approval_ot_from,

           sttd.approval_ot_to,

           hop.state,

           he.allowance_jemputan,

           hoe.meals,

           hoe.meals_cash,

           hoe.is_cancel,

           sttd.date_in,

           sttd.aot1,

           sttd.aot2,

           sttd.aot3,

           sttd.aot4,

           case

               when he.allowance_ot = true then 'OT'

               when he.allowance_ot1 = true then 'OT 1'

               when he.allowance_ot_flat = true then 'OT Flat'

               else 'None'
               end                                       as overtime

    from hr_overtime_planning hop

             join hr_overtime_employees hoe on hop.id = hoe.planning_id

             join hr_tmsentry_summary hts on hts.employee_id = hoe.employee_id

             join hr_employee he on hts.employee_id = he.id

             left join sb_tms_tmsentry_details sttd
                       on hoe.employee_id = sttd.employee_id and hoe.plann_date_from = sttd.details_date

    where hts.periode_id = period

      and hts.area_id = l_area

      and hts.branch_id = branch;


    -- monitoring overtime
-- hapus dari sb_employee_overtime
    delete from sb_employee_overtime where period_id = period;

-- insert sb_employee_overtime
    INSERT INTO public.sb_employee_overtime (area_id,
                                             branch_id,
                                             department_id,
                                             employee_id,
                                             attendee_total,
                                             job_id,
                                             create_uid,
                                             write_uid,
                                             nik,
                                             create_date,
                                             write_date,
                                             net_salary,
                                             pharma_allowance,
                                             work_allowance,
                                             family_allowance,
                                             salary_total,
                                             aot1,
                                             aot2,
                                             aot3,
                                             aot4,
                                             rp_aot1,
                                             rp_aot2,
                                             rp_aot3,
                                             rp_aot4,
                                             aot_total,
                                             salary_allowance_total,
                                             aot_salary_percentage,
                                             period_id,
                                             period_from,
                                             period_to)
    SELECT hts.area_id,
           hts.branch_id,
           hts.department_id,
           hts.employee_id,
           hts.attendee_total,
           hts.job_id,
           88                                                                                                  AS create_uid,
           88                                                                                                  AS write_uid,
           hts.nik,
           NOW()                                                                                               AS create_date,
           NOW()                                                                                               AS write_date,
           NULL                                                                                                AS net_salary,
           NULL                                                                                                AS pharma_allowance,
           NULL                                                                                                AS work_allowance,
           NULL                                                                                                AS family_allowance,
           NULL                                                                                                AS salary_total,
           sttd.aot1,
           sttd.aot2,
           sttd.aot3,
           sttd.aot4,
           NULL                                                                                                AS rp_aot1,
           NULL                                                                                                AS rp_aot2,
           NULL                                                                                                AS rp_aot3,
           NULL                                                                                                AS rp_aot4,
           (COALESCE(sttd.aot1, 0) + COALESCE(sttd.aot2, 0) + COALESCE(sttd.aot3, 0) + COALESCE(sttd.aot4, 0)) AS aot_total,
           NULL                                                                                                AS salary_allowance_total,
           NULL                                                                                                AS aot_salary_percentage,
           hts.periode_id,
           sttd.plann_date_from,
           sttd.plann_date_to
    FROM hr_tmsentry_summary hts
             JOIN sb_tms_tmsentry_details sttd
                  ON hts.id = sttd.tmsentry_id
    WHERE sttd.aot1 IS NOT NULL
      AND hts.periode_id = period;

END;

$procedure$
;
