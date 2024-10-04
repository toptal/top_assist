#!/usr/bin/env bash

self="${BASH_SOURCE[0]}"

common_dir="$(cd "$(dirname "$self")" && pwd)"
bin_dir="$(dirname "$common_dir")"
app_dir="$(dirname "$bin_dir")"

terminal_supports_colors() {
  command -v tput > /dev/null 2>&1 && [[ $(tput colors) -gt 8 ]]
  return $?
}

if terminal_supports_colors; then
  COLOR_RED='\033[0;31m'
  COLOR_YELLOW='\033[0;33m'
  COLOR_BLUE='\033[0;34m'
  COLOR_NC='\033[0m' # No Color
else
  unset COLOR_RED COLOR_YELLOW COLOR_NC
fi

info() {
  echo -e "${COLOR_BLUE}${*}${COLOR_NC}"
}

log_error() {
  echo -e "${COLOR_RED}${*}${COLOR_NC}"
}

doctor() {
  if ! [[ "$(poetry env info --path)" == *"$app_dir"* ]]; then
    log_error "Your poetry path ('poetry env info --path') is not using the local .venv folder, please remove and then run 'poetry install' again, see: https://python-poetry.org/docs/configuration/#virtualenvsin-project"
    exit 1
  fi
}

setup_prometheus_multiproc_dir() {
  if [ -n "$PROMETHEUS_MULTIPROC_DIR" ]; then
    rm -rf $PROMETHEUS_MULTIPROC_DIR
    mkdir -p $PROMETHEUS_MULTIPROC_DIR
  fi
}

exec_sql() {
  statement=$1
  docker compose exec -e PGPASSWORD=$DB_PASSWORD db psql -h localhost -U $DB_USER top_assist -tc "$statement"
}

setup_pg_database() {
  database_name=$1

  if ! exec_sql "SELECT 1 FROM pg_database WHERE datname = '$database_name'" | grep -q 1; then
      info "Creating $database_name"
      exec_sql "CREATE DATABASE $database_name"
  fi
}
