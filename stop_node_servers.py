#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import signal
import platform

def get_node_processes():
    """Retrieve running Node.js processes with PID and command line."""
    try:
        if platform.system() == "Windows":
            # Windows: Use tasklist command
            cmd = 'tasklist /FI "IMAGENAME eq node.exe" /FO CSV /NH'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            processes = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('","')
                    if len(parts) >= 2:
                        pid = parts[1].strip('"')
                        name = parts[0].strip('"')
                        if name.lower() == "node.exe":
                            processes.append((pid, "node.exe"))
            return processes
        else:
            # Unix-like: Use ps command
            cmd = "ps -eo pid,command | grep -E 'node |nodejs ' | grep -v grep"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            processes = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.strip().split(maxsplit=1)
                    if len(parts) >= 2:
                        pid = parts[0]
                        command = parts[1]
                        if command.startswith(('node ', 'nodejs ')) or 'node ' in command:
                            processes.append((pid, command))
            return processes
    except Exception as e:
        print(f"Error finding processes: {e}")
        return []

def terminate_process(pid):
    """Terminate a process by PID with graceful shutdown attempt, returning True if process is dead."""
    try:
        pid = int(pid)
        
        # Check if process is already dead
        if not process_exists(pid):
            return True
        
        # Try graceful termination first
        if platform.system() == "Windows":
            subprocess.run(['taskkill', '/PID', str(pid)], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGTERM)
        
        # Wait for process to exit
        time.sleep(2)
        
        # Check if dead after graceful termination
        if not process_exists(pid):
            return True
        
        # If still running, force kill
        if platform.system() == "Windows":
            subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGKILL)
        
        # Wait for force kill to take effect
        time.sleep(1)
        
        # Final check if process is dead
        return not process_exists(pid)
    except Exception as e:
        # After exception, check if process is dead
        if not process_exists(pid):
            return True
        print(f"Error terminating process {pid}: {e}")
        return False

def process_exists(pid):
    """Check if a process with given PID exists."""
    try:
        if platform.system() == "Windows":
            cmd = f'tasklist /FI "PID eq {pid}" /FO CSV /NH'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)  # Signal 0 doesn't kill but checks existence
            return True
    except:
        return False

def main():
    print("Node.js Process Terminator")
    print("==========================")
    
    # Get running Node.js processes
    processes = get_node_processes()
    
    if not processes:
        print("No running Node.js processes found.")
        return
    
    # Display processes
    print("\nFound running Node.js processes:")
    print("{:<8} {}".format("PID", "Command"))
    print("-" * 50)
    for pid, command in processes:
        print("{:<8} {}".format(pid, command[:60] + '...' if len(command) > 60 else command))
    
    # User selection
    print("\nOptions:")
    print("1. Terminate all processes")
    print("2. Terminate specific processes (by PID)")
    print("3. Cancel")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        # Terminate all processes
        print("\nTerminating all Node.js processes...")
        success_count = 0
        for pid, _ in processes:
            if terminate_process(pid):
                success_count += 1
        print(f"\nTerminated {success_count}/{len(processes)} processes successfully.")
    
    elif choice == "2":
        # Terminate specific processes
        pids_input = input("\nEnter PIDs to terminate (comma-separated): ").strip()
        selected_pids = [pid.strip() for pid in pids_input.split(',') if pid.strip()]
        
        if not selected_pids:
            print("No valid PIDs entered.")
            return
        
        print("\nTerminating selected processes...")
        success_count = 0
        for pid in selected_pids:
            if any(pid == p[0] for p in processes):
                if terminate_process(pid):
                    success_count += 1
            else:
                print(f"PID {pid} not found in Node.js processes.")
        print(f"\nTerminated {success_count}/{len(selected_pids)} processes successfully.")
    
    elif choice == "3":
        print("\nOperation cancelled.")
        return
    
    else:
        print("\nInvalid choice. Operation cancelled.")
        return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
