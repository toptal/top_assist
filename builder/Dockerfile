FROM python:3.12.2-slim-bookworm AS base

WORKDIR /app

ENV PROMETHEUS_MULTIPROC_DIR=tmp/prometheus_multiproc

RUN mkdir -p $PROMETHEUS_MULTIPROC_DIR
RUN mkdir -p /app/tmp

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential git libpq-dev curl \
  && apt-get purge -y --auto-remove \
  && rm -rf /var/lib/apt/lists/*

# --------------------------------------------

FROM base AS base_with_dependencies

RUN pip install --upgrade --no-cache pip setuptools wheel poetry

# See https://python-poetry.org/docs/faq#poetry-busts-my-docker-cache-because-it-requires-me-to-copy-my-source-files-in-before-installing-3rd-party-dependencies
COPY pyproject.toml poetry.lock poetry.toml /app/
RUN poetry install --only main --no-root --no-directory

# --------------------------------------------

FROM base_with_dependencies AS ci

# install dev dependencies (base image only have production ones)
RUN poetry install --no-root --no-directory
COPY . /app/
RUN poetry install

CMD ["poetry", "about"]

# --------------------------------------------

FROM base AS production

ARG USERNAME=topassist
ENV USERNAME=$USERNAME

ARG GID=1001
ENV GID=$GID

ARG UID=1001
ENV UID=$UID

RUN addgroup --gid $GID $USERNAME && \
    adduser --uid $UID --gid $GID --disabled-password --gecos "" $USERNAME

# Ownership
# tmp/ - owned by topassist user
# All other files - owned by root
#
# Permissions
# All directories - r-x access
# bin/ - r-x access
# tmp/ - full access (rwx)
# required python scripts (e.g. alembic) - r-x access
# All other files - read access (r--)

ENV VIRTUAL_ENV=/app/.venv PATH="/app/.venv/bin:$PATH"
COPY --chmod=644 --from=base_with_dependencies ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY --chmod=644 . /app/

ENV TMP_FOLDER=/app/tmp
ENV BIN_FOLDER=/app/bin
ENV PYTHON_SCRIPTS="/app/.venv/bin/alembic"

RUN chmod +x $(find /app -type d) && \
    chmod -R 655 $BIN_FOLDER && \
    chmod -R 755 $TMP_FOLDER && \
    chmod 655 $PYTHON_SCRIPTS && \
    chown -R $USERNAME:$USERNAME $TMP_FOLDER

USER $USERNAME

CMD ["bin/cli"]
