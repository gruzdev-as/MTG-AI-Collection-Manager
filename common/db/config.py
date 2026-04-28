import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PostgresConfig:
    """Configure PostgreSQL connection."""

    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    db: str = os.getenv("POSTGRES_DB", "postgres")
    host: str = os.getenv("POSTGRES_HOST", "postgres")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))

    @property
    def url(self) -> str:
        """Construct SQLAlchemy connection string."""
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def alt_url(self) -> str:
        """Construct raw Postgres URL without psycopg2."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
