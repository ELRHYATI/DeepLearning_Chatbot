#!/bin/bash
# Script to clean Java crash logs and other log files

echo "Cleaning log files..."

# Delete Java crash logs
rm -f hs_err_pid*.log
rm -f replay_pid*.log

# Delete other log files
rm -f *.log

echo "Log files cleaned!"

