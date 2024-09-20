### ASYNC API

#### Асинхронный API для кинотеатра

____________________________________________________________________________
Как запустить проект и проверить его работу
____________________________________________________________________________
 
Необходимо заполнить .env по шаблону .env_example

Запуск приложения с docker compose
```
docker-compose up --build
or
docker-compose up --build -d
```
____________________________________________________________________________
Запуск приложения для локальной разработки
____________________________________________________________________________
```
1. cd fastapi-solutions

2. python3.12 -m venv venv

3. source venv/bin/activate

4. pip3 install poetry

5. poetry install (or python -m poetry install)

6. docker run -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" krissmelikova/awesome_repository:v1

7. docker run -p 6379:6379 redis:7.2.4-alpine
 
8. gunicorn src.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

____________________________________________________________________________
Тестирование
____________________________________________________________________________

Локальное тестирование

```
1. docker run -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" krissmelikova/awesome_repository:v1

2. docker run -p 6379:6379 redis:7.2.4-alpine

3. (from fastapi-solutions directory) gunicorn src.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

4. cd tests/functional
```

Запустить все тесты
```
python3 -m pytest
```
Запустить все тесты в конкретном файле
```
python3 -m pytest src/<file with tests>
```

Запустить один конкретный тест
```
python3 -m pytest -k <test_name>
```
