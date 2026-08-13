from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central app configuration, loaded from environment variables / .env.
    Keeping this in one place means secrets never get hardcoded elsewhere.
    """
    database_url: str = "postgresql://billwise:billwise@localhost:5432/billwise"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    openai_api_key: str = ""

    # Email / SMTP settings (Week 6)
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = "noreply@billwise.app"
    mail_from_name: str = "BillWise"
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    # How many days before due date to send a reminder (0 = disable)
    reminder_days_before: int = 3

    class Config:
        env_file = ".env"


settings = Settings()
