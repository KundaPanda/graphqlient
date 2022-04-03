#!/bin/bash

function run {
  docker run --name graphqlient-test-mock-server --rm -d -v "$(pwd)/tests/graphql-faker:/mock" -p 127.0.0.1:9002:9002 apisguru/graphql-faker:latest /mock/schema.graphql
  poetry install
  sleep 5
  poetry run python -m pytest
}

tests=$(trap run EXIT)
echo "Stopping docker container $tests"
docker stop graphqlient-test-mock-server



