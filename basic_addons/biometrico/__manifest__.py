# -*- encoding: utf-8 -*-
{
	'name': 'Biometrico',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['planilla','resource','mail'],
	'version': '1.0',
	'description':"""
	Modulo para obtener los registros de biometrico zk utilizando un ip y un puerto.
	Para instalar este modulo es necesario agregar la lib de python zklib ubicada en la raiz de este modulo.
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
			'security/biometrico_security.xml',
			'security/ir.model.access.csv',
			'hr_attendance.xml',
			'hr_lack_period.xml',
			'biometrico.xml',
			'hr_attendance_period.xml',
			'hr_justification.xml',
			'hr_job_group.xml',
			'hr_calendar.xml',
			'hr_reports_config.xml'],
	'installable': True
}
