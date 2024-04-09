from django.apps import AppConfig

class NeowaveConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'neowave'

	def ready(self):
		import neowave.signals