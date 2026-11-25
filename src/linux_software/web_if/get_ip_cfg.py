#! /usr/bin/python3
import json

try:
    with open("ip_cfg.json", "r", encoding="utf-8") as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {}

print("Content-type: application/json")
print()
print(json.dumps(data))