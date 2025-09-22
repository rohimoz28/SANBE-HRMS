CREATE OR REPLACE PROCEDURE generate_update_role()
    language plpgsql
as
$$
BEGIN
    -- Hapus isi fix_ir_model_access
DELETE FROM fix_ir_model_access;

-- Copy isi terbaru dari ir_model_access ke fix_ir_model_access
INSERT INTO fix_ir_model_access
SELECT * FROM ir_model_access;
END;
$$;