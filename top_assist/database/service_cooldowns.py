from top_assist.models.service_cooldown import ServiceCooldownORM
from top_assist.utils.service_cooldown import ServiceCooldownState, ServiceCooldownStorage

from .database import get_db_session


class ServiceCooldownDatabaseStorage(ServiceCooldownStorage):
    """Storage implementation for service cooldowns using a database."""

    def write(self, service_key: str, cooldown: float) -> None:
        """Writes or updates the cooldown value for a given service key in the database.

        Args:
            service_key (str): The key of the external service.
            cooldown (float): The cooldown duration in seconds.
        """
        with get_db_session() as session:
            record = session.query(ServiceCooldownORM).filter_by(service_key=service_key).first()
            if record:
                record.cooldown_seconds = cooldown
                session.flush()
            else:
                session.add(ServiceCooldownORM(service_key=service_key, cooldown_seconds=cooldown))

    def read(self, service_key: str) -> ServiceCooldownState | None:
        """Reads the cooldown value for a given service key from the database.

        Args:
            service_key (str): The key of the external service.

        Returns:
            ServiceCooldownState | None: The cooldown state for the service key.
        """
        with get_db_session() as session:
            record = session.query(ServiceCooldownORM).filter_by(service_key=service_key).first()
            if not record:
                return None

            return ServiceCooldownState(
                cooldown_seconds=record.cooldown_seconds,
                timestamp=record.updated_at,
            )
