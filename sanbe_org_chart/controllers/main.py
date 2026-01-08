# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers import main

import logging
_logger = logging.getLogger(__name__)

class OrgChart(http.Controller):

	@http.route('/orgchart/update', methods=['POST'], csrf=False)
	def update_org_chart(self, child, last_parent, new_parent):
		if new_parent:
			emp = request.env['hr.department'].search([('id','=',child)])
			bawal = request.env['res.branch'].sudo().search([('id','=',child)])
			mybranch = request.env['res.branch'].sudo().search([('id','=',new_parent)])
			parent = request.env['hr.department'].search([('id','=',new_parent)])
			cekbranch = request.env['res.branch'].sudo().browse(int(parent.branch_id.id))
			emp.write({'parent_id': parent.id,'branch_id': mybranch.id})
		return ""

	@http.route('/orgchart/ondrop', type='json', auth="user")
	def ondrop_org_chart(self, employee_id):
		if employee_id:
			emp = request.env['hr.department'].search([('id','=',employee_id)])
			if emp:
				childs = request.env['hr.department'].search([('parent_id','=',emp.id)])
				if childs:
					childs_number = request.env['hr.department'].search_count([('parent_id','=',emp.id)])
					return {
						'name': 'Keep or Change Hierarchy',
						'type': 'ir.actions.act_window',
						'res_model': 'slife.employee',
						'view_mode': 'form',
						'view_type': 'form',
						'views': [[False, 'form']],
						'target': 'new',
						'context': {'parent_id': emp.id, 'childs_number': childs_number},
					}

		return {'result': False}
