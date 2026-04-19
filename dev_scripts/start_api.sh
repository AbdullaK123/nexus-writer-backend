#!/bin/bash

docker compose up --build -d nexus-writer

docker compose logs nexus-writer -f