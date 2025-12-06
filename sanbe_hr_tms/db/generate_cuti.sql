create or replace procedure generate_cuti()
    language plpgsql
as
$$
BEGIN
    -- 1. Update state = hold kalau employee belum approved
    UPDATE public.sb_leave_allocation_request
    SET state = 'hold'
    WHERE employee_id IN (
        SELECT id FROM hr_employee he WHERE he.state <> 'approved'
    );

    -- 2. Update state = running kalau employee approved
    UPDATE public.sb_leave_allocation_request
    SET state = 'running'
    WHERE employee_id IN (
        SELECT id FROM hr_employee he WHERE he.state = 'approved'
    );

    -- 3. Insert ke sb_leave_allocation_request untuk employee approved yang belum punya record
    INSERT INTO public.sb_leave_allocation_request
    (area_id, branch_id, department_id, job_id, employee_id, create_uid, write_uid, employee_levels, state)
    SELECT 
        he.area, 
        he.branch_id, 
        he.department_id, 
        he.job_id, 
        he.id, 
        CASE WHEN EXISTS (SELECT 1 FROM res_users WHERE id = 88) THEN 88 ELSE 2 END AS create_uid,
        CASE WHEN EXISTS (SELECT 1 FROM res_users WHERE id = 88) THEN 88 ELSE 2 END AS write_uid, 
        he.employee_levels, 
        'running'
    FROM hr_employee he
    WHERE he.state = 'approved'
      AND NOT EXISTS (
            SELECT 1
            FROM public.sb_leave_allocation_request sl
            WHERE sl.employee_id = he.id
      );

    -- 4. Insert benefit umum kecuali code = C3
    INSERT INTO sb_leave_benefit (
        leave_req_id, leave_master_id, create_uid, write_uid,
        "name", code, description, notes, start_date, end_date,
        create_date, write_date, total_leave_balance
    )
    SELECT a.id, slm.id, 86, 86, "name", code, NULL, NULL, NULL, NULL,
           now(), now(), days
    FROM sb_leave_allocation_request a
    JOIN sb_leave_master slm ON slm.code <> 'C3'
    WHERE NOT EXISTS (
        SELECT 1
        FROM sb_leave_benefit b
        WHERE b.leave_req_id = a.id
          AND b.leave_master_id = slm.id
    )
    ORDER BY code;

    -- 5. Insert khusus untuk C3 hanya untuk female
    INSERT INTO sb_leave_benefit (
        leave_req_id, leave_master_id, create_uid, write_uid,
        "name", code, description, notes, start_date, end_date,
        create_date, write_date, total_leave_balance
    )
    SELECT a.id, slm.id, 86, 86, slm."name", code, NULL, NULL, NULL, NULL,
           now(), now(), days
    FROM sb_leave_allocation_request a
    JOIN sb_leave_master slm ON slm.code = 'C3'
    JOIN hr_employee he ON he.id = a.employee_id AND he.gender = 'female'
    WHERE NOT EXISTS (
        SELECT 1
        FROM sb_leave_benefit b
        WHERE b.leave_req_id = a.id
          AND b.leave_master_id = slm.id
    )
    ORDER BY code;

    -- 6. Update total_leave = total_leave_balance
    UPDATE sb_leave_allocation_request a
    SET total_leave = b.total_leave_balance
    FROM (
        SELECT leave_req_id, total_leave_balance
        FROM sb_leave_benefit
    ) b
    WHERE a.id = b.leave_req_id;

END;
$$;

-- alter procedure generate_cuti() owner to odoo;

