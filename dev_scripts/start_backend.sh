#!/bin/bash

docker compose up --build -d

docker compose logs nexus-writer -f