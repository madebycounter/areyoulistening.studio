import json
import os

with open(os.environ['AYL_CONFIG'], 'r') as f:
    config = json.load(f)