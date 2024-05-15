### ASYNC API

#### Асинхронный API для кинотеатра

____________________________________________________________________________

Добработки по ETL

[Added ETL for persons](https://github.com/KrisMelikova/new_admin_panel_sprint_3/commit/fce4ba8595ed0ed0b20773bcc14cacd19a37e9ad)

[Added ETL for genres](https://github.com/KrisMelikova/new_admin_panel_sprint_3/commit/d6e4d749a94bcf7225e14fbbd33646c3c6999d58)

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

Запуск приложения для локальной разработки
```
1. cd fastapi-solutions

2. python3.12 -m venv venv

3. source venv/bin/activate

4. pip3 install poetry

5. poetry install

6. docker run -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" krissmelikova/awesome_repository:v1

7. docker run -p 6379:6379 redis:7.2.4-alpine
 
8. gunicorn src.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```