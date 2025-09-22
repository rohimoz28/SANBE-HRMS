from odoo import models, api
import logging
_logger = logging.getLogger(__name__)

class HrTmsInit(models.Model):
    _name = "hr.tms.init"
    _description = "Model ini berisi kode / query yang dijalankan setelah upgrade modul TMS"

    @api.model
    def init(self):
        """
        Fungsi ini dipanggil setiap kali module upgrade/reload registry.
        Akan menjalankan kode / query yang ada di method class ini.
        """
        self._run_after_upgrade_query()

    def _run_after_upgrade_query(self):
        """
        Helper: jalankan procedure generate_after_upgrade().
        Query ini dijalankan untuk memperbaiki hak akses user
        yang berubah setelah upgrade modul TMS
        """
        try:
            self.env.cr.execute("CALL generate_after_upgrade();")
            _logger.warning("✅ Successfully executed generate_after_upgrade()")
        except Exception as e:
            _logger.error(f"❌ Error executing generate_after_upgrade: {e}")