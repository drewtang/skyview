from django.apps import AppConfig


class IngestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ingestion'

    def ready(self):
        import ingestion.tasks  # Import tasks when app is ready
