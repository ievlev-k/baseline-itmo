#!/usr/bin/bash

curl -X POST \
-H "Content-Type: application/json" \
-d '{"name":"qwen2.5:7b"}' \
http://localhost:11434/api/pull