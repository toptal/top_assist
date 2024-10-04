import top_assist.utils.tracer  # noqa: F401,RUF100 we need to import this before annything else to properly load the built-in instrumentations
from top_assist.utils.logging.configure import configure_logging
from top_assist.utils.sentry_notifier import configure_sentry

configure_logging()
configure_sentry()

from top_assist.database.service_cooldowns import ServiceCooldownDatabaseStorage  # noqa: E402
from top_assist.utils.service_cooldown import configure_service_cooldown  # noqa: E402

configure_service_cooldown(ServiceCooldownDatabaseStorage())
