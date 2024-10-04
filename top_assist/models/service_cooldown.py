from .base import Base, Mapped, int_pk, unique_string


class ServiceCooldownORM(Base):
    """SQLAlchemy model for storing external service cooldown state.

    Attr:
        id: The primary key of the service cooldown.
        service_key: The key of the external service.
        cooldown_seconds: The cooldown duration in seconds.
    """

    __tablename__ = "service_cooldowns"

    id: Mapped[int_pk]
    service_key: Mapped[unique_string]
    cooldown_seconds: Mapped[float]

    repr_cols_num = 3
