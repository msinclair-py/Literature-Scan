#!/bin/bash

# Number of attempts
attempt=0
max_attempts=5

# Target Unix timestamp to check against
target_timestamp=1953109629

# Function to run the Python script
run_script() {
    python run_arxiv_scraper.py -m 0
}

# Loop to ensure the script runs at least 20 times
while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    echo "Attempt $attempt"
    run_script
    
    # Check the current Unix timestamp
    current_timestamp=$(date +%s)
    if [ "$current_timestamp" -eq "$target_timestamp" ]; then
        echo "Current timestamp matches target timestamp. Exiting."
        exit 0
    fi
    
    # Check the exit status of the script
    if [ $? -ne 0 ]; then
        echo "Script failed. Relaunching..."
    else
        echo "Script succeeded."
    fi
    sleep 120
done

echo "Script has been run $max_attempts times."

