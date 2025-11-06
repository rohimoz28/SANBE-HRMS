CREATE OR REPLACE FUNCTION add_monthly_leave()
RETURNS void AS $$
BEGIN
    -- Cek apakah hari ini tanggal 1
    IF EXTRACT(DAY FROM CURRENT_DATE) = 1 THEN

        -- Tambah jatah cuti untuk karyawan yang statusnya approved dan code A1, hanya sekali per karyawan
        UPDATE sb_leave_benefit slb
        SET total_leave_balance = total_leave_balance + 1  -- contoh: nambah 1 hari tiap bulan
        FROM (
            SELECT DISTINCT he.id AS employee_id, slb.id AS leave_benefit_id
            FROM sb_leave_allocation_request slab
            JOIN sb_leave_allocation sla ON slab.employee_id = sla.employee_id
            JOIN sb_leave_benefit slb ON slb.leave_req_id = slab.id AND slb.code = 'A1'
            JOIN hr_employee he ON he.id = sla.employee_id AND he.state = 'approved'
        ) AS unique_employees
        WHERE slb.id = unique_employees.leave_benefit_id;

        -- Aktifkan jika memang harus diupdate leave_allocation di tabel sb_leave_allocation
        /*
        UPDATE sb_leave_allocation sla
        SET leave_allocation = eligible.total_leave_balance + 1
        --SET leave_allocation = leave_allocation + 1
        FROM (
            SELECT DISTINCT 
                sla.id AS leave_allocation_id,
                slb.total_leave_balance
            FROM sb_leave_allocation_request slab
            JOIN sb_leave_allocation sla ON slab.employee_id = sla.employee_id
            JOIN sb_leave_benefit slb ON slb.leave_req_id = slab.id AND slb.code = 'A1'
            JOIN hr_employee he ON he.id = sla.employee_id AND he.state = 'approved'
        ) AS eligible
        WHERE sla.id = eligible.leave_allocation_id;
        */

        -- Perintah insert data ke sb_leave_tracking
        /*
        INSERT INTO public.sb_leave_tracking
        (leave_req_id, create_uid, write_uid, remarks, "date", description, create_date, write_date, leave_allocation, leave_used, leave_remaining, leave_master_id, permission_date_from, permission_date_to, permission_status)
        SELECT DISTINCT 
            slab.id,
            2,
            2,
            'Tambahan cuti Tahunan bulan ' || EXTRACT(MONTH FROM CURRENT_DATE),
            now()::date,
            NULL,
            now(),
            now(),
            slb.total_leave_balance + 1,
            0,
            slb.total_leave_balance + 1,
            5,
            NULL,
            NULL,
            'approved'
        FROM sb_leave_allocation_request slab
        JOIN sb_leave_allocation sla ON slab.employee_id = sla.employee_id
        JOIN sb_leave_benefit slb ON slb.leave_req_id = slab.id AND slb.code = 'A1'
        JOIN hr_employee he ON he.id = sla.employee_id AND he.state = 'approved';
        */

    END IF;

END;
$$ LANGUAGE plpgsql;
