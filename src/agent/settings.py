from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from agent.models import AppReport

REQUIRED_MODEL = "mistralai/mistral-7b-instruct"
REQUIRED_MODEL_FREE = "mistralai/mistral-7b-instruct:free"


class QuerySettings(BaseModel):
    evidence_row_cap: int = 30


class SchemaSummarySettings(BaseModel):
    sample_values_cap: int = 10
    profile_columns_cap: int = 50


class RefreshSettings(BaseModel):
    default_stale_after_hours: int = 24


class AppConfig(BaseModel):
    app_name: str
    reports: list[dict[str, Any]] = Field(default_factory=list)
    allowed_tables: list[str] = Field(default_factory=list)
    join_hints: list[str] = Field(default_factory=list)
    business_definitions: dict[str, str] = Field(default_factory=dict)
    refresh: RefreshSettings = Field(default_factory=RefreshSettings)
    query: QuerySettings = Field(default_factory=QuerySettings)
    schema_summary: SchemaSummarySettings = Field(default_factory=SchemaSummarySettings)

    @property
    def report_models(self) -> list[AppReport]:
        parsed: list[AppReport] = []
        for report in self.reports:
            parsed.append(
                AppReport(
                    name=report["name"],
                    report_link_name=report["report_link_name"],
                    table_name=report["table_name"],
                    description=report.get("description", ""),
                    key_columns=report.get("key_columns", []),
                )
            )
        return parsed


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default=REQUIRED_MODEL_FREE, alias="OPENROUTER_MODEL")

    zoho_client_id: str | None = Field(default=None, alias="ZOHO_CLIENT_ID")
    zoho_client_secret: str | None = Field(default=None, alias="ZOHO_CLIENT_SECRET")
    zoho_refresh_token: str | None = Field(default=None, alias="ZOHO_REFRESH_TOKEN")
    zoho_account_owner: str | None = Field(default=None, alias="ZOHO_ACCOUNT_OWNER")
    zoho_app_link_name: str | None = Field(default=None, alias="ZOHO_APP_LINK_NAME")
    zoho_accounts_url: str = Field(default="https://accounts.zoho.com", alias="ZOHO_ACCOUNTS_URL")
    zoho_base_url: str = Field(default="https://www.zohoapis.com", alias="ZOHO_BASE_URL")
    zoho_creator_base_url: str = Field(default="https://creator.zoho.com", alias="ZOHO_CREATOR_BASE_URL")

    workspace_dir: Path = Path.cwd()

    @model_validator(mode="after")
    def validate_model_lock(self) -> "Settings":
        allowed = {REQUIRED_MODEL, REQUIRED_MODEL_FREE}
        if self.openrouter_model not in allowed:
            raise ValueError(
                f"OPENROUTER_MODEL must be one of {sorted(allowed)}. Got '{self.openrouter_model}'."
            )
        return self


def load_app_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return AppConfig.model_validate(data)


def load_settings() -> Settings:
    load_dotenv()
    return Settings()
