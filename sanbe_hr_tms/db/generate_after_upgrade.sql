CREATE OR REPLACE PROCEDURE generate_after_upgrade()
    language plpgsql
as
$$
BEGIN
    -- Update data dari fix_ir_model_access ke ir_model_access
UPDATE ir_model_access a
SET model_id   = b.model_id,
    group_id   = b.group_id,
    active     = b.active,
    perm_read  = b.perm_read,
    perm_write = b.perm_write,
    perm_create= b.perm_create,
    perm_unlink= b.perm_unlink
    FROM fix_ir_model_access b
WHERE a.id = b.id;

-- Hapus isi fix_ir_model_access
DELETE FROM fix_ir_model_access;

-- Copy isi terbaru dari ir_model_access ke fix_ir_model_access
INSERT INTO fix_ir_model_access
SELECT * FROM ir_model_access;
END;
$$;