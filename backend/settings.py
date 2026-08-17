from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class Settings(BaseSettings):
    database_hostname: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    database_uri: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_use_tls: bool

    model_config = SettingsConfigDict(
        env_file=r"C:\@me\Sustainable_Product_Ideation\backend\.env", extra="ignore"
    )


class Collections(str, Enum):
    USER = "User"
    ORGANIZATION = "Organization"
    BOARDS = "Boards"
    AHP_SHEETS = "AhpSheets"
    SESSIONS = "Sessions"
    EMAIL_SERVICE = "EmailService"
    FORGOT_PASSWORD = "ForgotPassword"
    


settings = Settings()
