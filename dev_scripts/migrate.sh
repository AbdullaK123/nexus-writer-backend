#!/bin/bash

docker compose exec nexus-writer uv run aerich migrate --name "$1"