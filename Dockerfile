FROM python:3.10-slim-bullseye as builder
# See https://github.com/python-poetry/poetry/discussions/1879#discussioncomment-216865
# for inspiration
COPY poetry.lock pyproject.toml ./

# Envrironment Configuration
## See https://github.com/alejandro-angulo/poetry/blob/master/docs/configuration.md
# Determine where to install poetry
ENV POETRY_HOME=/opt/poetry

# Install Poetry & generate a requirements.txt file
RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())' | python && \
    "$POETRY_HOME/bin/poetry" export -f requirements.txt > requirements.txt

# FROM python:3.9.16-slim-bullseye
FROM python:3.10.10-alpine3.17

WORKDIR /app
COPY --from=builder requirements.txt pyproject.toml ./

# Install app's external dependencies
RUN apk add --no-cache ffmpeg

# Pre emptively add the user's bin folder to PATH
ENV PATH="/root/.local/bin:$PATH"

# ENV PATH /root/.local/bin:$PATH

# COPY pyproject.toml .
# COPY poetry.lock .

# Install from source code
# copy whole source code folder
COPY src src
# copy README.rst since it is required ffrom pyproject.toml (for pip install)
COPY README.rst .

RUN pip install --upgrade pip && pip install --no-cache-dir .

CMD [ "create-album" ]



# RUN apt-get update && \
#     apt-get install -y --no-install-recommends build-essential && \
#     pip install -U pip && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/* && \
#     pip install --no-cache-dir --user -r requirements.txt

# COPY . .
# RUN pip install --no-cache-dir --user .

# CMD [ "generate-python" ]



# FROM python:3.10.10-alpine3.17 AS build

# # RUN apt-get update && update install ffmpeg && apt clean

