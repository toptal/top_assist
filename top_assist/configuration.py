import json
import os


def __bool_env(env: str, default: str = "true") -> bool:
    return os.environ.get(env, default).lower() in ("true", "yes", "1")


def json_env_list(env: str, default: str = "[]") -> list:
    """Parses a JSON array from environment variables and ensures it's a list of dictionaries."""
    value = os.environ.get(env, default).strip()
    return json.loads(value if value else default)


environment = os.environ.get("ENV", "development")

# DB configuration
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_NAME = os.environ["DB_NAME"]
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Vector database configuration
vector_collections_prefix = os.environ["VECTOR_COLLECTIONS_PREFIX"]
pages_certainty_threshold = float(os.environ.get("PAGES_CERTAINTY_THRESHOLD", "0.0"))

qdrant_url = os.environ.get("QDRANT_URL")

weaviate_http_host = os.environ.get("WEAVIATE_HTTP_HOST")
weaviate_http_port = int(os.environ.get("WEAVIATE_HTTP_PORT", "80"))
weaviate_grpc_host = os.environ.get("WEAVIATE_GRPC_HOST")
weaviate_grpc_port = int(os.environ.get("WEAVIATE_GRPC_PORT", "50051"))
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")
weaviate_secure = __bool_env("WEAVIATE_SECURE")
weaviate_client_skip_init_checks = __bool_env("WEAVIATE_CLIENT_SKIP_INIT_CHECKS", default="false")

if not all([qdrant_url]) and not all([weaviate_http_host, weaviate_grpc_host]):
    raise NotImplementedError("Either Qdrant or Weaviate must be configured.")

# Confluence configuration
confluence_base_url = os.environ["CONFLUENCE_BASE_URL"]

# cloudid for the confluence account, to be used in the OAUTH flow, see: https://developer.atlassian.com/cloud/confluence/oauth-2-3lo-apps/#3-1-get-the-cloudid-for-your-site
confluence_cloud_id = os.environ["CONFLUENCE_CLOUD_ID"]

if not confluence_base_url.endswith("/"):
    confluence_base_url += "/"
confluence_username = os.environ["CONFLUENCE_USER"]
confluence_api_token = os.environ["CONFLUENCE_API_TOKEN"]
confluence_ignore_labels = [
    f'"{label}"' for label in os.environ.get("CONFLUENCE_IGNORE_LABELS", "top-assist-ignore").split(",") if label
]

# Initial URL to start the OAuth flow with Top assist on Confluence, useful if you have frontpage/proxy and need to access Top Assist before the Conflunce OAuth page
confluence_oauth_top_assist_redirect_url_template = os.environ["CONFLUENCE_OAUTH_TOP_ASSIST_REDIRECT_URL_TEMPLATE"]

# Confluence OAUth Page URL, this one includes the required scopes for the Top Asssit OAuth app
#
# Current scopes:
#
#   * confluence:search - To be able to check which pages the user has access to
#   * offline_access - required to generate an refresh token
#
# See more at https://developer.atlassian.com/cloud/confluence/oauth-2-3lo-apps/
confluence_oauth_authorization_url_template = os.environ["CONFLUENCE_OAUTH_AUTHORIZATION_URL_TEMPLATE"]
# Callback URL, it will be called by confluence OAuth page after the user authorize the Top Assist OAuth app
confluence_oauth_redirect_uri = os.environ["CONFLUENCE_OAUTH_REDIRECT_URI"]

# OAuth credentials from the Confluence OAuth app
confluence_oauth_client_id = os.environ["CONFLUENCE_OAUTH_CLIENT_ID"]
confluence_oauth_client_secret = os.environ["CONFLUENCE_OAUTH_CLIENT_SECRET"]

# Confluence page with stats data about Top Assist available spaces and pages
confluence_stats_page_title = os.environ["CONFLUENCE_STATS_PAGE_TITLE"]
confluence_stats_page_id = os.environ["CONFLUENCE_STATS_PAGE_ID"]

# Slack configuration
slack_app_level_token = os.environ["SLACK_APP_TOKEN"]
slack_bot_user_oauth_token = os.environ["SLACK_BOT_TOKEN"]
slack_allow_enterprise_id = os.environ["SLACK_ALLOW_ENTERPRISE_ID"]
slack_allow_team_id = os.environ["SLACK_ALLOW_TEAM_ID"]
slack_reply_questions_in_channels = __bool_env("SLACK_REPLY_QUESTIONS_IN_CHANNELS", default="false")
slack_listener_workers_num = int(os.environ.get("TOP_ASSIST_SLACK_LISTENER_WORKERS_NUM", "4"))

# OpenAI configuration
open_ai_api_key = os.environ["OPENAI_API_KEY"]

# Assistant IDs
qa_assistant_id = os.environ["OPENAI_ASSISTANT_ID_QA"]
base_assistant_id = os.environ["OPENAI_ASSISTANT_ID_BASE"]

# Model IDs
# Doesn't apply for assistants
# Assistants have as part of the assistant the model id
model_id = "gpt-4o"
model_id_mini = "gpt-4o-mini"

# Embedding model IDs
embedding_model_id = os.environ.get("TOP_ASSIST_EMBEDDING_MODEL_ID", "text-embedding-3-large")
embedding_workers_num = int(os.environ.get("TOP_ASSIST_EMBEDDING_WORKERS_NUM", "10"))
embedding_chunk_size = int(os.environ.get("TOP_ASSIST_EMBEDDING_CHUNK_SIZE", "500"))
embedding_chunk_sleep_seconds = int(os.environ.get("TOP_ASSIST_EMBEDDING_CHUNK_SLEEP_SECONDS", "10"))

# page retrieval for answering questions
# document count is recommended from 3 to 15 where 3 is minimum cost and 15 is maximum comprehensive answer
question_context_pages_count = 5

# Logs
logs_file = os.environ.get("TOP_ASSIST_LOGS_FILE")
logs_format = os.environ.get("TOP_ASSIST_LOGS_FORMAT", "text")
logs_level = os.environ.get("TOP_ASSIST_LOGS_LEVEL", "INFO")
logs_text_color_enable = __bool_env("TOP_ASSIST_LOGS_TEXT_COLOR", default="false")

# Datadog
dd_log_injection = __bool_env("DD_LOGS_INJECTION", default="false")

# Sentry
sentry_dsn = os.environ.get("SENTRY_DSN", "")

# Services cooldowns
service_cooldown_initial_seconds = float(os.environ.get("SERVICE_COOLDOWN_INITIAL_SECONDS", "5"))
service_cooldown_max_attempts = int(os.environ.get("SERVICE_COOLDOWN_MAX_ATTEMPTS", "5"))
service_cooldown_recovery_factor = float(os.environ.get("SERVICE_COOLDOWN_RECOVERY_FACTOR", "0.5"))
service_cooldown_exp_base = float(os.environ.get("SERVICE_COOLDOWN_EXP_BASE", "1.5"))

# Key for encrypting personal Confluence tokens
cryptography_secret_key = os.environ["CRYPTOGRAPHY_SECRET_KEY"]

# API configuration
api_host = os.environ["TOP_ASSIST_API_HOST"]
api_port = int(os.environ["TOP_ASSIST_API_PORT"])

# API Docs
api_docs_url = os.environ.get("TOP_ASSIST_API_DOCS_URL", None)
api_redocs_url = os.environ.get("TOP_ASSIST_API_REDOCS_URL", None)

# Admin Config
admin_user = os.environ["TOP_ASSIST_ADMIN_USER"]
admin_password = os.environ["TOP_ASSIST_ADMIN_PASSWORD"]
admin_session_secret_key = os.environ["TOP_ASSIST_ADMIN_SESSION_SECRET_KEY"]
admin_extra_links = json_env_list("TOP_ASSIST_ADMIN_EXTRA_LINKS")

# Metrics configuration
metrics_port = int(os.environ["TOP_ASSIST_METRICS_PORT"])
metrics_port_auto_increment = __bool_env("TOP_ASSIST_METRICS_PORT_AUTOINCREMENT", default="false")

# Dify
dify_api_endpoint = os.environ["DIFY_API_ENDPOINT"]
dify_prompt_optimizer_api_key = os.environ.get("DIFY_PROMPT_OPTIMIZER_API_KEY")
