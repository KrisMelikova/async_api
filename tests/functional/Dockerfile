FROM fastapi-image

WORKDIR /tests/functional/

COPY poetry.lock pyproject.toml /tests/functional/

RUN poetry config virtualenvs.create false && poetry install

COPY . .

RUN chmod u+x commands.sh

CMD ["/bin/sh", "/tests/functional/commands.sh"]