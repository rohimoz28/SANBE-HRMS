from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'Inherit Res Users to Add some method'

    def _run_after_upgrade_query(self):
        """
        jalankan procedure generate_after_upgrade().
        """
        try:
            self.env.cr.execute("CALL generate_after_upgrade();")
            _logger.warning(">>> INIT CALLED ON UPDATE USER ACCESS <<<")
            _logger.warning("✅ Successfully executed generate_after_upgrade()")
        except Exception as e:
            _logger.error(f"❌ Error executing generate_after_upgrade: {e}")

    def _run_generate_update_role(self):
        """
        jalankan procedure generate_after_upgrade().
        """
        try:
            self.env.cr.execute("CALL generate_update_role();")
            _logger.warning(">>> INIT CALLED ON UPDATE USER ACCESS <<<")
            _logger.warning("✅ Successfully executed generate_update_role()")
        except Exception as e:
            _logger.error(f"❌ Error executing generate_update_role: {e}")

    def write(self, vals):
        """
        Override write: dipanggil saat user update akses user
        pada menu Setting -> User & Companies -> Users
        """
        res = super().write(vals)

        self._run_after_upgrade_query()
        self._run_generate_update_role()

        return res

