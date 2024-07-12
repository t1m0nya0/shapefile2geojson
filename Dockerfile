FROM python:3.11-slim-buster AS base

# DEPENDENCY STAGE
FROM base AS builder

# install poetry
RUN pip install poetry==1.3.2 && poetry config virtualenvs.create true && poetry config virtualenvs.in-project true

# install dependencies
WORKDIR /app/
COPY poetry.lock pyproject.toml /app/
RUN poetry install --no-dev --no-interaction --no-ansi --no-root

# FINAL STAGE
FROM base AS production

WORKDIR /app/

COPY . /app/

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin/:$PATH"
ENV PYTHONPATH="/app/"

CMD ["flask", "run", "--host=0.0.0.0"]
