#!/bin/bash

docker compose down nexus-writer

docker compose up --build -d nexus-writer

docker compose logs nexus-writer -f