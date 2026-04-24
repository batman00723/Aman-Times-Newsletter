from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    secret_key: SecretStr
    debug : bool

    db_name: str
    db_user: str
    db_password: SecretStr
    db_host: str
    db_port: str
    db_url: SecretStr
    
    jwt_access_lifetime_mins: int = 60

    google_api_key: SecretStr
    cerebras_api_key: SecretStr
    tavily_api_key: SecretStr

    langsmith_api_key: SecretStr
    langsmith_tracing: str = "true"
    langsmith_project: str 
    langsmith_endpoint: str 

   
    email_host: str = 'smtp.gmail.com'
    email_port: int = 587
    email_use_tls: bool = True
    email_host_user: str = 'batmanmishra23@gmail.com'
    email_host_password: SecretStr

    model_config= SettingsConfigDict(env_file= ".env",
                                     extra= 'ignore')

settings= Settings()