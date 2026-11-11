from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: SecretStr | None = None
    mongo_database: str | None = None
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS debe incluir al menos un origen.")
        if "*" in origins:
            raise ValueError("CORS_ORIGINS no permite el origen comodín '*'.")
        for origin in origins:
            parsed = urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(
                    "Cada origen CORS debe ser una URL absoluta HTTP o HTTPS."
                )
            if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
                raise ValueError(
                    "Los orígenes CORS no deben incluir rutas, consultas ni fragmentos."
                )
        return ",".join(origins)

    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def mongo_configuration(self) -> tuple[str, str]:
        if self.mongo_uri is None or self.mongo_database is None:
            raise RuntimeError(
                "Configura MONGO_URI y MONGO_DATABASE en el archivo .env."
            )
        database = self.mongo_database.strip()
        if not database:
            raise RuntimeError("MONGO_DATABASE no puede estar vacío.")
        return self.mongo_uri.get_secret_value(), database


@lru_cache
def get_settings() -> Settings:
    return Settings()
