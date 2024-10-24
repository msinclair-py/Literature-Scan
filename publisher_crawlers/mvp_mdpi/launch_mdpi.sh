#!/bin/bash

# Run the python script 30 times with a 5-minute wait between each run
for i in {1..30}
do
    echo "Running iteration $i"
    if python run_mpdi_spyder.py; then
        echo "Iteration $i completed successfully."
    else
        echo "Iteration $i failed. Retrying..."
    fi
    echo "Waiting for 5 minutes before the next run..."
    sleep 300 # 300 seconds = 5 minutes
done

