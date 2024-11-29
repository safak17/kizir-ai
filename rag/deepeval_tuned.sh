#!/bin/bash

# Directory containing CSV files
CSV_FOLDER="param_results"  # Replace with the path to your folder
DEEPEVAL_CACHE=".deepeval-cache.json"

# Check if the folder exists
if [ ! -d "$CSV_FOLDER" ]; then
  echo "Error: Folder $CSV_FOLDER does not exist."
  exit 1
fi

# Iterate over all CSV files in the folder
for csv_file in "$CSV_FOLDER"/*.csv; do
  if [ -f "$csv_file" ]; then
    echo "Processing file: $csv_file"
    
    # Run the Python script with the current CSV file
    python3 deepeval_param.py  "$csv_file"
    
    # Check if the cache file exists
    if [ -f "$DEEPEVAL_CACHE" ]; then
      # Get the base name of the current CSV file (without path or extension)
      base_name=$(basename "$csv_file" .csv)
      
      # Rename the .deepeval_cache.json file to match the CSV file
      mv "$DEEPEVAL_CACHE" "${base_name}_deepeval_cache.json"
      echo "Saved cache as: ${base_name}_deepeval_cache.json"
    else
      echo "Warning: Cache file $DEEPEVAL_CACHE not found after processing $csv_file"
    fi
  else
    echo "Warning: No CSV files found in $CSV_FOLDER"
  fi
done
