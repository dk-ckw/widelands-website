from django_messages.apps import DjangoMessagesConfig
from django.db.models import signals


class WLDjangoMessagesConfig(DjangoMessagesConfig):

    #name = 'django_messages'
    #verbose_name = 'Messages'

    def ready(self):
        from django_messages_wl.management import create_notice_types
        signals.post_migrate.connect(create_notice_types, sender=self)    