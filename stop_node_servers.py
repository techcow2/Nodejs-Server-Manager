#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import signal
import platform
import threading
import queue

# Import platform-specific modules for character input
if platform.system() == "Windows":
    import msvcrt
else:
    import termios
    import tty
    import select

# Color constants for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def display_header():
    # Define the content lines
    content_lines = [
        "Nodejs Server Killer by techcow2",
        "https://github.com/techcow2",
        "copyright 2025 MIT License"
    ]
    
    # Find the longest line to determine box width
    max_line_length = max(len(line) for line in content_lines)
    box_width = max_line_length + 10  # Add padding on both sides
    
    # Ensure minimum width for aesthetics
    box_width = max(box_width, 60)
    
    # Create box components
    top_border = Colors.HEADER + "╔" + "═" * (box_width) + "╗" + Colors.ENDC
    bottom_border = Colors.HEADER + "╚" + "═" * (box_width) + "╝" + Colors.ENDC
    
    # Create empty line with padding
    empty_line = Colors.HEADER + "║" + " " * (box_width) + "║" + Colors.ENDC
    
    # Create content lines with padding
    content_box_lines = []
    for line in content_lines:
        # Calculate padding to center the text
        padding = (box_width - len(line)) // 2
        padded_line = Colors.HEADER + "║" + " " * padding + Colors.BOLD + Colors.OKCYAN + line + Colors.ENDC + Colors.HEADER + " " * (box_width - len(line) - padding) + "║" + Colors.ENDC
        content_box_lines.append(padded_line)
    
    # Combine all parts
    header = "\n".join([
        top_border,
        empty_line,
        *content_box_lines,
        empty_line,
        bottom_border
    ])
    
    print(header)

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
        print(f"{Colors.FAIL}Error finding processes: {e}{Colors.ENDC}")
        return []

def terminate_process(pid, command=None):
    """Terminate a process by PID with graceful shutdown attempt, returning status information."""
    try:
        pid = int(pid)
        
        # Check if process is already dead
        if not process_exists(pid):
            return {
                'pid': pid,
                'command': command,
                'status': 'already_terminated',
                'message': f"Process {pid} was already terminated"
            }
        
        # Display initial termination message
        cmd_display = f" ({command})" if command else ""
        print(f"{Colors.WARNING}Terminating process {pid}{cmd_display}...{Colors.ENDC}")
        
        # Try graceful termination first
        print(f"{Colors.OKCYAN}  Attempting graceful shutdown...{Colors.ENDC}")
        if platform.system() == "Windows":
            subprocess.run(['taskkill', '/PID', str(pid)], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGTERM)
        
        # Wait for process to exit
        time.sleep(2)
        
        # Check if dead after graceful termination
        if not process_exists(pid):
            return {
                'pid': pid,
                'command': command,
                'status': 'success',
                'message': f"Process {pid}{cmd_display} terminated gracefully"
            }
        
        # If still running, force kill
        print(f"{Colors.WARNING}  Graceful shutdown failed, attempting force kill...{Colors.ENDC}")
        if platform.system() == "Windows":
            subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGKILL)
        
        # Wait for force kill to take effect
        time.sleep(1)
        
        # Final check if process is dead
        if not process_exists(pid):
            return {
                'pid': pid,
                'command': command,
                'status': 'success_force',
                'message': f"Process {pid}{cmd_display} terminated forcefully"
            }
        else:
            return {
                'pid': pid,
                'command': command,
                'status': 'failed',
                'message': f"Failed to terminate process {pid}{cmd_display}"
            }
    except Exception as e:
        # After exception, check if process is dead
        if not process_exists(pid):
            return {
                'pid': pid,
                'command': command,
                'status': 'success',
                'message': f"Process {pid}{cmd_display} terminated (with exception)"
            }
        return {
            'pid': pid,
            'command': command,
            'status': 'error',
            'message': f"Error terminating process {pid}{cmd_display}: {e}"
        }

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

def display_termination_report(results):
    """Display a report of termination results."""
    if not results:
        print(f"{Colors.WARNING}No processes were terminated.{Colors.ENDC}")
        return
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}=== TERMINATION REPORT ==={Colors.ENDC}")
    
    # Count results by status
    success_count = sum(1 for r in results if r['status'] in ['success', 'success_force'])
    failed_count = sum(1 for r in results if r['status'] in ['failed', 'error'])
    already_terminated_count = sum(1 for r in results if r['status'] == 'already_terminated')
    
    # Show summary
    print(f"{Colors.OKCYAN}Total processes: {len(results)}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Successfully terminated: {success_count}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed to terminate: {failed_count}{Colors.ENDC}")
    print(f"{Colors.WARNING}Already terminated: {already_terminated_count}{Colors.ENDC}")
    
    # Show successful terminations
    successful = [r for r in results if r['status'] in ['success', 'success_force']]
    if successful:
        print(f"\n{Colors.BOLD}{Colors.OKGREEN}SUCCESSFULLY TERMINATED:{Colors.ENDC}")
        for result in successful:
            cmd_display = f" ({result['command']})" if result['command'] else ""
            status_msg = "gracefully" if result['status'] == 'success' else "forcefully"
            print(f"{Colors.OKGREEN}  PID {result['pid']}{cmd_display} - terminated {status_msg}{Colors.ENDC}")
    
    # Show failed terminations
    failed = [r for r in results if r['status'] in ['failed', 'error']]
    if failed:
        print(f"\n{Colors.BOLD}{Colors.FAIL}FAILED TO TERMINATE:{Colors.ENDC}")
        for result in failed:
            cmd_display = f" ({result['command']})" if result['command'] else ""
            print(f"{Colors.FAIL}  PID {result['pid']}{cmd_display} - {result['message']}{Colors.ENDC}")
    
    # Show already terminated
    already = [r for r in results if r['status'] == 'already_terminated']
    if already:
        print(f"\n{Colors.BOLD}{Colors.WARNING}ALREADY TERMINATED:{Colors.ENDC}")
        for result in already:
            cmd_display = f" ({result['command']})" if result['command'] else ""
            print(f"{Colors.WARNING}  PID {result['pid']}{cmd_display} - was already terminated{Colors.ENDC}")

class InputHandler:
    """Handles keyboard input for both Windows and Unix-like systems."""
    def __init__(self):
        self.input_queue = queue.Queue()
        self.current_input = ""
        self.running = True
        
    def get_char(self):
        """Get a single character from stdin without blocking."""
        if platform.system() == "Windows":
            return self._get_char_windows()
        else:
            return self._get_char_unix()
    
    def _get_char_windows(self):
        """Get a single character on Windows."""
        if msvcrt.kbhit():
            char = msvcrt.getch()
            # Handle special keys
            if char == b'\xe0':  # Special key prefix
                char = msvcrt.getch()  # Get the actual key code
                return None  # Ignore special keys for now
            return char.decode('utf-8')
        return None
    
    def _get_char_unix(self):
        """Get a single character on Unix-like systems."""
        # Save current terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            # Set terminal to raw mode
            tty.setraw(sys.stdin.fileno())
            
            # Check if there's input available
            if select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                return char
            return None
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    def input_thread(self):
        """Thread function to handle user input."""
        while self.running:
            char = self.get_char()
            if char:
                self.input_queue.put(char)
            time.sleep(0.01)  # Small sleep to prevent high CPU usage
    
    def start(self):
        """Start the input thread."""
        self.thread = threading.Thread(target=self.input_thread)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the input thread."""
        self.running = False
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1)
    
    def process_input(self):
        """Process input characters and update current_input."""
        try:
            while True:
                try:
                    char = self.input_queue.get_nowait()
                    
                    if char == '\r':  # Enter key
                        # Return the current input and clear it
                        cmd = self.current_input
                        self.current_input = ""
                        return cmd
                    
                    elif char == '\x03':  # Ctrl+C
                        return 'q'  # Treat as quit
                    
                    elif char == '\x08' or char == '\x7f':  # Backspace or Delete
                        # Remove last character
                        if self.current_input:
                            self.current_input = self.current_input[:-1]
                    
                    elif char == '\x1b':  # Escape sequence (arrow keys, etc.)
                        # For now, just ignore escape sequences
                        pass
                    
                    elif ord(char) >= 32:  # Printable characters
                        # Add character to current input
                        self.current_input += char
                
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error processing input: {e}")
        
        return None

def live_monitoring_mode():
    """Enter live monitoring mode to continuously watch for Node.js processes."""
    print(f"\n{Colors.OKCYAN}Entering live monitoring mode...{Colors.ENDC}")
    print(f"\n{Colors.OKGREEN}Starting monitoring... (Press Enter after typing commands){Colors.ENDC}")
    
    # Track processes we've seen
    known_processes = set()
    
    # Create input handler
    input_handler = InputHandler()
    input_handler.start()
    
    try:
        last_refresh = time.time()
        refresh_interval = 2  # seconds
        message = ""
        message_time = 0
        show_termination_report = False
        termination_results = []
        termination_report_drawn = False
        termination_report_time = 0
        termination_report_timeout = 10  # seconds to show termination report before returning to monitoring
        last_termination_report_draw = 0  # Track when we last drew the termination report
        
        while True:
            current_time = time.time()
            
            # Process input
            command = input_handler.process_input()
            
            if command:
                if command == 'q':
                    print(f"{Colors.WARNING}Exiting live monitoring mode.{Colors.ENDC}")
                    break
                
                elif command == 'h':
                    message = f"{Colors.OKBLUE}Help information is always visible at the bottom of the screen.{Colors.ENDC}"
                    message_time = current_time
                
                elif command == 'r':
                    message = f"{Colors.OKBLUE}Refreshing process list...{Colors.ENDC}"
                    message_time = current_time
                    last_refresh = 0  # Force immediate refresh
                    show_termination_report = False  # Hide termination report on refresh
                    termination_report_drawn = False  # Reset termination report state
                
                elif command == 'k':
                    # Kill all processes
                    current_processes = get_node_processes()
                    current_pids = {pid for pid, _ in current_processes}
                    
                    message = f"{Colors.WARNING}Terminating all Node.js processes...{Colors.ENDC}"
                    message_time = current_time
                    termination_results = []
                    for pid, command in current_processes:
                        result = terminate_process(pid, command)
                        termination_results.append(result)
                        if result['status'] in ['success', 'success_force', 'already_terminated']:
                            known_processes.discard(pid)
                    
                    # Set flag to show termination report
                    show_termination_report = True
                    termination_report_drawn = False  # Reset draw state
                    termination_report_time = current_time  # Set the time when report was shown
                    last_termination_report_draw = 0  # Reset last draw time
                    
                    # Update message with summary
                    success_count = sum(1 for r in termination_results if r['status'] in ['success', 'success_force'])
                    message = f"{Colors.OKGREEN}Terminated {success_count}/{len(current_processes)} processes. Returning to monitoring in {termination_report_timeout} seconds...{Colors.ENDC}"
                    message_time = current_time
                    last_refresh = current_time  # Update refresh time but don't force refresh immediately
                
                elif command.startswith('k '):
                    # Kill specific process
                    target = command[2:].strip()
                    
                    # Check if user tried to use "k all"
                    if target == 'all':
                        message = f"{Colors.FAIL}Use 'k' to kill all processes, not 'k all'.{Colors.ENDC}"
                        message_time = current_time
                        continue
                    
                    current_processes = get_node_processes()
                    current_pids = {pid for pid, _ in current_processes}
                    
                    if target in current_pids:
                        # Find the command for this PID
                        command = next((cmd for pid, cmd in current_processes if pid == target), None)
                        
                        message = f"{Colors.WARNING}Terminating process {target}...{Colors.ENDC}"
                        message_time = current_time
                        
                        result = terminate_process(target, command)
                        termination_results = [result]  # Store as list for consistent handling
                        
                        if result['status'] in ['success', 'success_force', 'already_terminated']:
                            known_processes.discard(target)
                        
                        # Set flag to show termination report
                        show_termination_report = True
                        termination_report_drawn = False  # Reset draw state
                        termination_report_time = current_time  # Set the time when report was shown
                        last_termination_report_draw = 0  # Reset last draw time
                        
                        # Display result
                        if result['status'] in ['success', 'success_force']:
                            message = f"{Colors.OKGREEN}Process {target} terminated successfully. Returning to monitoring in {termination_report_timeout} seconds...{Colors.ENDC}"
                        elif result['status'] == 'already_terminated':
                            message = f"{Colors.WARNING}Process {target} was already terminated. Returning to monitoring in {termination_report_timeout} seconds...{Colors.ENDC}"
                        else:
                            message = f"{Colors.FAIL}Failed to terminate process {target}. Returning to monitoring in {termination_report_timeout} seconds...{Colors.ENDC}"
                        
                        message_time = current_time
                        last_refresh = current_time  # Update refresh time but don't force refresh immediately
                    else:
                        message = f"{Colors.FAIL}PID {target} not found in current processes.{Colors.ENDC}"
                        message_time = current_time
                
                else:
                    message = f"{Colors.FAIL}Invalid command. See available commands at the bottom of the screen.{Colors.ENDC}"
                    message_time = current_time
            
            # Handle termination report display if active
            if show_termination_report:
                # Check if timeout has passed
                timeout_remaining = termination_report_timeout - (current_time - termination_report_time)
                
                if timeout_remaining <= 0:
                    # Timeout reached, return to monitoring
                    show_termination_report = False
                    termination_report_drawn = False
                    last_refresh = 0  # Force immediate refresh
                    continue
                
                # Only redraw if necessary (first time, every second, or message is active)
                if (not termination_report_drawn or 
                    current_time - last_termination_report_draw > 1 or 
                    (message and current_time - message_time < 5)):
                    
                    # Clear screen
                    os.system('cls' if platform.system() == 'Windows' else 'clear')
                    
                    # Display header
                    display_header()
                    
                    # Display monitoring status
                    print(f"\n{Colors.BOLD}{Colors.HEADER}=== LIVE MONITORING MODE ==={Colors.ENDC}")
                    print(f"{Colors.OKCYAN}Still monitoring - Showing termination report{Colors.ENDC}")
                    print(f"{Colors.WARNING}Returning to live monitoring in {int(timeout_remaining)} seconds...{Colors.ENDC}")
                    
                    # Display termination report
                    display_termination_report(termination_results)
                    
                    # Show message if active
                    if message and current_time - message_time < 5:
                        print(f"\n{message}\n")
                    
                    # Show command reference (simplified)
                    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*50}{Colors.ENDC}")
                    print(f"{Colors.BOLD}{Colors.OKCYAN}AVAILABLE COMMANDS:{Colors.ENDC}")
                    print(f"{Colors.OKCYAN}  r           - {Colors.OKBLUE}Return to monitoring now{Colors.ENDC}")
                    print(f"{Colors.OKCYAN}  h           - {Colors.OKBLUE}Show this help{Colors.ENDC}")
                    print(f"{Colors.OKCYAN}  q           - {Colors.WARNING}Quit monitoring mode{Colors.ENDC}")
                    print(f"{Colors.BOLD}{Colors.HEADER}{'='*50}{Colors.ENDC}")
                    
                    # Show command prompt
                    print(f"\n{Colors.BOLD}Enter command: {Colors.ENDC}", end='', flush=True)
                    
                    termination_report_drawn = True
                    last_termination_report_draw = current_time
                
                # Skip the rest of the loop to avoid unnecessary processing
                time.sleep(0.1)
                continue
            
            # Refresh display if needed (only in live monitoring mode)
            if current_time - last_refresh >= refresh_interval:
                # Clear screen
                os.system('cls' if platform.system() == 'Windows' else 'clear')
                
                # Display header
                display_header()
                
                # Get current processes
                current_processes = get_node_processes()
                current_pids = {pid for pid, _ in current_processes}
                
                # Detect new processes
                new_processes = []
                for pid, command in current_processes:
                    if pid not in known_processes:
                        new_processes.append((pid, command))
                        known_processes.add(pid)
                
                # Detect terminated processes
                terminated_pids = known_processes - current_pids
                for pid in terminated_pids:
                    known_processes.remove(pid)
                
                # Display status
                print(f"\n{Colors.BOLD}{Colors.HEADER}=== LIVE MONITORING MODE ==={Colors.ENDC}")
                print(f"{Colors.OKCYAN}Monitoring {len(current_pids)} Node.js processes{Colors.ENDC}")
                
                # Show message if recent
                if message and current_time - message_time < 5:
                    print(f"\n{message}\n")
                
                # Show new processes
                if new_processes:
                    print(f"\n{Colors.BOLD}{Colors.OKGREEN}NEW PROCESSES DETECTED:{Colors.ENDC}")
                    print(f"{Colors.OKCYAN}{'PID':<8} {'Command'}{Colors.ENDC}")
                    print(f"{Colors.OKCYAN}{'-' * 50}{Colors.ENDC}")
                    for pid, command in new_processes:
                        print(f"{Colors.OKCYAN}{pid:<8} {command[:60] + '...' if len(command) > 60 else command}{Colors.ENDC}")
                
                # Show terminated processes
                if terminated_pids:
                    print(f"\n{Colors.BOLD}{Colors.FAIL}PROCESSES TERMINATED:{Colors.ENDC}")
                    for pid in terminated_pids:
                        print(f"{Colors.FAIL}  PID {pid}{Colors.ENDC}")
                
                # Show all current processes
                print(f"\n{Colors.BOLD}{Colors.OKBLUE}CURRENT NODE.JS PROCESSES:{Colors.ENDC}")
                print(f"{Colors.OKCYAN}{'PID':<8} {'Command'}{Colors.ENDC}")
                print(f"{Colors.OKCYAN}{'-' * 50}{Colors.ENDC}")
                if not current_processes:
                    print(f"{Colors.WARNING}No Node.js processes running.{Colors.ENDC}")
                else:
                    for pid, command in current_processes:
                        print(f"{Colors.OKCYAN}{pid:<8} {command[:60] + '...' if len(command) > 60 else command}{Colors.ENDC}")
                
                # Always show command reference
                print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*50}{Colors.ENDC}")
                print(f"{Colors.BOLD}{Colors.OKCYAN}AVAILABLE COMMANDS:{Colors.ENDC}")
                print(f"{Colors.OKCYAN}  k           - {Colors.WARNING}Kill all processes{Colors.ENDC}")
                print(f"{Colors.OKCYAN}  k <pid>     - {Colors.WARNING}Kill process with specified PID{Colors.ENDC}")
                print(f"{Colors.OKCYAN}  r           - {Colors.OKBLUE}Refresh process list{Colors.ENDC}")
                print(f"{Colors.OKCYAN}  h           - {Colors.OKBLUE}Show this help{Colors.ENDC}")
                print(f"{Colors.OKCYAN}  q           - {Colors.WARNING}Quit monitoring mode{Colors.ENDC}")
                print(f"{Colors.BOLD}{Colors.HEADER}{'='*50}{Colors.ENDC}")
                
                # Show command prompt with current input
                print(f"\n{Colors.BOLD}Enter command: {Colors.ENDC}{input_handler.current_input}", end='', flush=True)
                
                last_refresh = current_time
            
            # Small sleep to prevent high CPU usage
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Exiting live monitoring mode.{Colors.ENDC}")
    finally:
        # Ensure input handler is stopped
        input_handler.stop()

def main():
    display_header()
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}Node.js Process Terminator{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}=========================={Colors.ENDC}")
    
    # Get running Node.js processes
    processes = get_node_processes()
    
    if not processes:
        print(f"{Colors.WARNING}No running Node.js processes found.{Colors.ENDC}")
    
    # Display processes
    if processes:
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}Found running Node.js processes:{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'PID':<8} {'Command'}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'-' * 50}{Colors.ENDC}")
        for pid, command in processes:
            print(f"{Colors.OKCYAN}{pid:<8} {command[:60] + '...' if len(command) > 60 else command}{Colors.ENDC}")
    
    # User selection
    print(f"\n{Colors.BOLD}{Colors.HEADER}Options:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}1. {Colors.WARNING}Terminate all processes{Colors.ENDC}")
    print(f"{Colors.OKCYAN}2. {Colors.WARNING}Terminate specific processes (by PID){Colors.ENDC}")
    print(f"{Colors.OKCYAN}3. {Colors.OKBLUE}Live monitoring mode{Colors.ENDC}")
    print(f"{Colors.OKCYAN}4. {Colors.WARNING}Cancel{Colors.ENDC}")
    
    choice = input(f"\n{Colors.BOLD}Enter your choice (1-4): {Colors.ENDC}").strip()
    
    if choice == "1":
        # Terminate all processes
        if not processes:
            print(f"\n{Colors.WARNING}No Node.js processes to terminate.{Colors.ENDC}")
            return
            
        print(f"\n{Colors.WARNING}Terminating all Node.js processes...{Colors.ENDC}")
        termination_results = []
        for pid, command in processes:
            result = terminate_process(pid, command)
            termination_results.append(result)
        
        # Display termination report
        display_termination_report(termination_results)
    
    elif choice == "2":
        # Terminate specific processes
        if not processes:
            print(f"\n{Colors.WARNING}No Node.js processes to terminate.{Colors.ENDC}")
            return
            
        pids_input = input(f"\n{Colors.BOLD}Enter PIDs to terminate (comma-separated): {Colors.ENDC}").strip()
        selected_pids = [pid.strip() for pid in pids_input.split(',') if pid.strip()]
        
        if not selected_pids:
            print(f"{Colors.FAIL}No valid PIDs entered.{Colors.ENDC}")
            return
        
        print(f"\n{Colors.WARNING}Terminating selected processes...{Colors.ENDC}")
        termination_results = []
        for pid in selected_pids:
            # Find the command for this PID
            command = next((cmd for p, cmd in processes if p == pid), None)
            if command is not None:
                result = terminate_process(pid, command)
                termination_results.append(result)
            else:
                termination_results.append({
                    'pid': pid,
                    'command': None,
                    'status': 'not_found',
                    'message': f"PID {pid} not found in Node.js processes"
                })
        
        # Display termination report
        display_termination_report(termination_results)
    
    elif choice == "3":
        # Live monitoring mode
        live_monitoring_mode()
    
    elif choice == "4":
        print(f"\n{Colors.WARNING}Operation cancelled.{Colors.ENDC}")
        return
    
    else:
        print(f"\n{Colors.FAIL}Invalid choice. Operation cancelled.{Colors.ENDC}")
        return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Operation cancelled by user.{Colors.ENDC}")
        sys.exit(0)
