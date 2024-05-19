FROM fastapi-image

WORKDIR /tests/functional/

COPY poetry.lock pyproject.toml /tests/functional/

RUN poetry config virtualenvs.create false && poetry install

COPY . .

CMD ["pytest"]