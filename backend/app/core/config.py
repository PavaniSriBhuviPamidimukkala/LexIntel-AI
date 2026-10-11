from pathlib import Path
from ipaddress import ip_network
from pydantic import SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str

    DATABASE_URL: str

    EMBEDDING_MODEL: str
    VECTOR_DIMENSION: int


    # LLM Configuration
    LLM_PROVIDER: str
    GEMINI_MODEL: str
    OLLAMA_MODEL: str

    GEMINI_API_KEY: SecretStr | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024
    SQL_ECHO: bool = False
    ENVIRONMENT: str = "development"
    AUTH_MODE: str = "disabled"
    TRUSTED_PROXY_CIDRS: list[str] = []

    @model_validator(mode="after")
    def validate_runtime_settings(self):
        if not self.DATABASE_URL.strip():
            raise ValueError("DATABASE_URL must not be empty.")

        if self.MAX_UPLOAD_SIZE_BYTES <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_BYTES must be greater than zero.")

        if not self.CORS_ALLOWED_ORIGINS:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS must include at least one trusted origin."
            )

        if self.AUTH_MODE not in {"disabled", "proxy"}:
            raise ValueError("AUTH_MODE must be either 'disabled' or 'proxy'.")

        try:
            proxy_networks = [
                ip_network(cidr, strict=False)
                for cidr in self.TRUSTED_PROXY_CIDRS
            ]
        except ValueError as exc:
            raise ValueError(
                "TRUSTED_PROXY_CIDRS must contain valid IP networks."
            ) from exc

        if self.AUTH_MODE == "proxy" and not proxy_networks:
            raise ValueError(
                "TRUSTED_PROXY_CIDRS is required when AUTH_MODE is 'proxy'."
            )

        if (
            self.ENVIRONMENT.casefold() in {"production", "prod"}
            and self.AUTH_MODE != "proxy"
        ):
            raise ValueError(
                "AUTH_MODE must be 'proxy' in production deployments."
            )

        if self.LLM_PROVIDER.casefold() == "gemini":
            api_key = (
                self.GEMINI_API_KEY.get_secret_value().strip()
                if self.GEMINI_API_KEY
                else ""
            )
            placeholders = {
                "your_api_key",
                "replace-me",
                "change-me",
            }
            if (
                not api_key
                or api_key.casefold() in placeholders
                or api_key.casefold().startswith("replace-with-")
            ):
                raise ValueError(
                    "GEMINI_API_KEY must contain a valid key when "
                    "LLM_PROVIDER is set to gemini."
                )

        return self

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


try:
    settings = Settings()
except ValidationError as exc:
    missing = sorted(
        {
            str(error["loc"][0])
            for error in exc.errors()
            if error["type"] == "missing"
        }
    )
    if missing:
        raise RuntimeError(
            "Missing required backend environment variables: "
            + ", ".join(missing)
        ) from None
    details = "; ".join(
        f"{'.'.join(str(part) for part in error['loc']) or 'settings'}: "
        f"{error['msg']}"
        for error in exc.errors(include_input=False)
    )
    raise RuntimeError(
        "Invalid backend environment configuration: " + details
    ) from None