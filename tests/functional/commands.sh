#!/bin/bash
python3 /tests/functional/utils/wait_for_es.py
python3 /tests/functional/utils/wait_for_redis.py
cd /tests/functional/
pytest