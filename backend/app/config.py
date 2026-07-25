"""
Configuracion central de la aplicacion.
Lee variables de entorno (o el archivo .env) usando pydantic-settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/mag_dashboard.db"

    kpi_categoria_ternero: str = "Terneros"
    kpi_categoria_novillo: str = "Novillos +430 kg"

    mag_base_url: str = "https://www.mercadoagroganadero.com.ar"

    semaforo_umbral_bajo: float = -8.0
    semaforo_umbral_alto: float = 8.0

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
