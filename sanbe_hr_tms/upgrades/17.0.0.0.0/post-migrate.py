import logging
_logger = logging.getLogger(__name__)

def migrate(cr, version):
    try:
        cr.execute("CALL generate_after_upgrade()")  # untuk procedure
        # cr.execute("SELECT generate_after_upgrade()")  # kalau function
        _logger.info("Successfully executed generate_after_upgrade() after upgrade")
    except Exception as e:
        _logger.error(f"Error executing generate_after_upgrade: {e}")
