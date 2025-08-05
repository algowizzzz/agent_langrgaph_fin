#!/bin/bash

echo "Starting BMO Documentation Analysis Tool Frontend..."
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting Streamlit app..."
streamlit run app.py