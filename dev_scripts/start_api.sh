#!/bin/bash

docker compose up -d nexus-writer

docker compose logs nexus-writer -f