# Node.js Server Manager

A simple PowerShell script to easily find and manage Node.js servers running on your system. Useful for developers who frequently start and stop local web servers and need to clean up orphaned processes.

## Features

- 🔍 **Scan** for all running Node.js processes and their listening ports
- 🎯 **Terminate** individual servers or all servers at once
- 🔄 **Refresh** the server list to see current status
- 🎨 **Color-coded** interface for better visibility
- 📱 **Number-based menu** for easy navigation
- 🧹 **Clean up** orphaned processes that don't appear in your terminal

## Why Use This?

When developing with Node.js, you might frequently encounter situations where:
- Servers continue running after closing the terminal
- Multiple servers are running on different ports
- You get port conflicts when starting new servers
- You need to manually hunt down processes in Task Manager

This tool solves these problems by providing a simple interface to manage all your Node.js servers in one place.

## Installation

1. Download the `node_manager.ps1` script
2. (Optional) Place it in a directory that's in your PATH for easy access
3. If you get execution policy errors, run PowerShell as Administrator and execute:
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## Usage

1. Run the script:
   ```powershell
   .\node_manager.ps1
   ```
2. Use the number-based menu:
   - `0` - Refresh server list
   - `1, 2, 3...` - Terminate individual servers
   - `999` - Terminate all servers
   - `9999` - Exit the program

## Example Output

```
=================================
   Node.js Server Manager v1.0
   Created by: github.com/techcow2
=================================

Scanning for running Node.js servers...

Found 2 Node.js server(s):
1. node.exe (PID: 1234, Addresses: 0.0.0.0:3000, [::]:3000)
2. node.exe (PID: 5678, Addresses: 0.0.0.0:3001, [::]:3001)

Menu Options:
  0. Refresh server list
  1. Terminate server 1 (PID: 1234)
  2. Terminate server 2 (PID: 5678)
  999. Terminate ALL servers
  9999. Exit program
```

## Requirements

- Windows PowerShell 5.1 or later
- Administrator privileges (recommended for process termination)

## License

MIT License - see LICENSE file for details

## Author

Created by [techcow2](https://github.com/techcow2)
```
