ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-alpine3.17 as builder
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

# receive security updates for 3.10.x
FROM python:${PYTHON_VERSION}-alpine3.17

WORKDIR /app
COPY --from=builder requirements.txt pyproject.toml ./

# Install app's external dependencies
RUN apk add --no-cache ffmpeg

# Pre emptively add the user's bin folder to PATH
ENV PATH="/root/.local/bin:$PATH"

# Install from source code
# copy whole source code folder
COPY src src
# copy README.rst since it is required by `pip install` (poetry or setuptools) backend
COPY README.rst .

RUN pip install --upgrade pip && pip install -r requirements.txt

RUN pip install --no-cache-dir .

CMD [ "create-album" ]
