# -*- coding: utf-8 -*-
from logging import getLogger
logger = getLogger('applications.dummy')

from os.path import join as pjoin, dirname
from tichy.application import Application
from tichy.tasklet import Sleep
from paroli.gui import ElementaryLayoutWindow

class Dummy(Application):
	name = 'Dummy'
	icon = 'icon.png'
	category = 'launcher' # So that we see the app in the launcher

	def run(self, parent=None, standalone=False):
		logger.info('run starts')
		edje_file = pjoin(dirname(__file__), 'dummy.edj')
		window = ElementaryLayoutWindow(edje_file, "dummy", None, None, True)
		message = '<h1>I`m a dummy</h1><p><strong>Hihi bla fasel</strong></p>'
		for n in range(5):
			message += '<p><red>We are at step %d</red></p>'% n
			window.main_layout.elm_obj.edje_get().part_text_set('dummy.textview', message)
			yield Sleep(1)
		window.delete()
		logger.info('run stops')
# vim:tw=0:nowrap
