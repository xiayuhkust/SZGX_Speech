#!/bin/bash
# Ensure we're using the system Python
/usr/local/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
