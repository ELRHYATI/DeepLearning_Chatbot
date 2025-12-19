"""
Utility to clean up Java crash logs and other log files
"""
import os
import glob
from pathlib import Path
from typing import List
import time


def clean_java_crash_logs(directory: str = ".") -> List[str]:
    """
    Clean Java crash logs (hs_err_pid*.log and replay_pid*.log)
    
    Args:
        directory: Directory to clean (default: current directory)
        
    Returns:
        List of deleted file paths
    """
    deleted_files = []
    directory_path = Path(directory).resolve()
    
    # Find and delete Java crash logs
    patterns = [
        "hs_err_pid*.log",
        "replay_pid*.log"
    ]
    
    for pattern in patterns:
        # Use glob for better pattern matching (non-recursive first)
        for log_file in directory_path.glob(pattern):
            try:
                # Check if file exists and is a file (not directory)
                if log_file.is_file():
                    log_file.unlink()
                    deleted_files.append(str(log_file))
            except PermissionError:
                # File might be locked, try again after a short delay
                try:
                    time.sleep(0.1)
                    if log_file.is_file():
                        log_file.unlink()
                        deleted_files.append(str(log_file))
                except Exception as e:
                    print(f"Could not delete {log_file} after retry: {e}")
            except Exception as e:
                print(f"Could not delete {log_file}: {e}")
    
    return deleted_files


def clean_all_logs(directory: str = ".") -> List[str]:
    """
    Clean all log files in directory
    
    Args:
        directory: Directory to clean (default: current directory)
        
    Returns:
        List of deleted file paths
    """
    deleted_files = []
    directory_path = Path(directory)
    
    # Find and delete all .log files
    for log_file in directory_path.glob("*.log"):
        try:
            log_file.unlink()
            deleted_files.append(str(log_file))
        except Exception as e:
            print(f"Could not delete {log_file}: {e}")
    
    return deleted_files


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        deleted = clean_all_logs()
    else:
        deleted = clean_java_crash_logs()
    
    if deleted:
        print(f"Cleaned {len(deleted)} log file(s):")
        for file in deleted:
            print(f"  - {file}")
    else:
        print("No log files found to clean.")

