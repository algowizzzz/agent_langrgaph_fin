#!/bin/bash

echo "Starting BMO Documentation Analysis Tool Backend..."
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting FastAPI server..."
python main.py