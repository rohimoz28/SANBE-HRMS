CREATE OR REPLACE PROCEDURE procedure_leave_alloc()
LANGUAGE plpgsql AS $$
BEGIN
    delete
    from sb_leave_allocation sla;

    WITH aa AS (
        SELECT
            name,
            id AS employee_id,
            he.join_date,
            he.job_status,
            area,
            he.branch_id,
            he.department_id,
            he.job_id
        FROM hr_employee he
        WHERE he.emp_status = 'confirmed'
          AND he.state = 'approved'
        /*AND he.job_status = 'contract' AND he.join_date IS NOT NULL*/
    ),
         bb AS (
             SELECT
--              aa.name,
aa.area,
aa.branch_id,
aa.department_id,
aa.job_id,
aa.employee_id,
--              aa.join_date,
--              aa.job_status,
calculate_leave_alloc(aa.join_date, CURRENT_DATE, aa.job_status) AS leave_allocation,
COALESCE(SUM(hpe.time_days) FILTER (WHERE hpe.is_approved = true), 0) AS leave_used
             FROM aa
                      LEFT JOIN hr_permission_entry hpe ON aa.employee_id = hpe.employee_id /*where hpe.is_approved is true*/
             GROUP BY aa.name, aa.employee_id,aa.area,aa.branch_id,aa.department_id,aa.job_id, aa.join_date, aa.job_status
         ),
         cc as (SELECT bb.*,bb.leave_allocation - bb.leave_used as remaining_leave, NOW() AS create_date FROM bb)
-- select * from cc;
    insert
    into sb_leave_allocation as sla (area_id,branch_id,department_id,job_id,employee_id,leave_allocation, leave_used, leave_remaining, create_date)
    select * from cc;
END;
$$;
