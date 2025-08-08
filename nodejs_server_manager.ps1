<#
Node.js Server Manager v1.0 by github.com/techcow2

Quickly find and stop Node.js servers running on your system.
Useful for developers who start/stop local web servers frequently
and need to clean up orphaned processes that don't appear in terminals.
#>

function Show-Header {
    Clear-Host
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host "   Node.js Server Manager v1.0   " -ForegroundColor Cyan
    Write-Host "   Created by: github.com/techcow2" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Find and manage Node.js servers running on your system." -ForegroundColor Gray
    Write-Host "Stops orphaned processes that don't appear in terminals." -ForegroundColor Gray
    Write-Host ""
}

function Get-NodeServers {
    Write-Host "Scanning for running Node.js servers..." -ForegroundColor Yellow
    Write-Host ""

    $servers = @()
    $processGroups = @{}
    
    # Get all node.exe processes
    $nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue

    if ($null -eq $nodeProcesses) {
        return $servers
    }

    # Convert single process to array if needed
    if ($nodeProcesses -is [System.Diagnostics.Process]) {
        $nodeProcesses = @($nodeProcesses)
    }

    # Group processes by PID (same PID = same server)
    foreach ($process in $nodeProcesses) {
        try {
            $netstat = netstat -ano | Select-String "LISTENING" | Select-String $process.Id.ToString()
            
            if ($netstat) {
                if ($processGroups.ContainsKey($process.Id)) {
                    # Add additional addresses to existing group
                    foreach ($line in $netstat) {
                        $address = ($line -split '\s+')[2]
                        if ($processGroups[$process.Id].Addresses -notcontains $address) {
                            $processGroups[$process.Id].Addresses += $address
                        }
                    }
                }
                else {
                    # Create new group
                    $addresses = @()
                    foreach ($line in $netstat) {
                        $address = ($line -split '\s+')[2]
                        $addresses += $address
                    }
                    $processGroups[$process.Id] = @{
                        Process = $process
                        Addresses = $addresses
                    }
                }
            }
        }
        catch {
            continue
        }
    }

    # Convert to server list with sequential numbering
    $count = 1
    foreach ($group in $processGroups.Values) {
        $server = [PSCustomObject]@{
            Index = $count
            Process = $group.Process
            Addresses = $group.Addresses
        }
        $servers += $server
        $count++
    }

    return $servers
}

function Show-Servers {
    param([array]$servers)
    
    if ($servers.Count -eq 0) {
        Write-Host "No Node.js servers found." -ForegroundColor Red
        return $false
    }

    Write-Host "Found $($servers.Count) Node.js server(s):" -ForegroundColor Green
    foreach ($server in $servers) {
        $addresses = ($server.Addresses -join ", ")
        Write-Host "$($server.Index). $($server.Process.ProcessName).exe (PID: $($server.Process.Id), Addresses: $addresses)" -ForegroundColor White
    }
    Write-Host ""
    return $true
}

function Show-Menu {
    param([array]$servers)
    
    Write-Host "Menu Options:" -ForegroundColor Yellow
    Write-Host "  0. Refresh server list" -ForegroundColor Gray
    
    # Show individual server options
    foreach ($server in $servers) {
        Write-Host "  $($server.Index). Terminate server $($server.Index) (PID: $($server.Process.Id))" -ForegroundColor Gray
    }
    
    if ($servers.Count -gt 0) {
        Write-Host "  999. Terminate ALL servers" -ForegroundColor Gray
    }
    Write-Host "  9999. Exit program" -ForegroundColor Gray
    Write-Host ""
}

function Stop-Server {
    param([System.Diagnostics.Process]$process, [string]$description)
    
    Write-Host "Terminating $description..." -ForegroundColor Yellow
    try {
        Stop-Process -Id $process.Id -Force -ErrorAction Stop
        Write-Host "  Success" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "  Failed - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main script
Show-Header

do {
    $servers = Get-NodeServers
    $hasServers = Show-Servers -servers $servers
    Show-Menu -servers $servers

    $choice = Read-Host "Enter option number"
    
    # Handle special menu options
    if ($choice -eq "0") {
        continue  # Refresh
    }
    elseif ($choice -eq "9999") {
        Write-Host "Goodbye!" -ForegroundColor Cyan
        exit 0
    }
    elseif ($choice -eq "999") {
        if ($hasServers) {
            Write-Host "Terminating all Node.js servers..." -ForegroundColor Yellow
            foreach ($server in $servers) {
                $addresses = ($server.Addresses -join ", ")
                Stop-Server -process $server.Process -description "$($server.Process.ProcessName).exe (PID: $($server.Process.Id), Addresses: $addresses)"
            }
            Write-Host ""
            Write-Host "All servers processed." -ForegroundColor Green
            Start-Sleep -Seconds 2
        } else {
            Write-Host "No servers to terminate." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
        continue
    }
    
    # Handle server termination by number (1, 2, 3, etc.)
    if ($choice -match "^\d+$" -and $choice -ne "0") {
        $index = [int]$choice
        $server = $servers | Where-Object { $_.Index -eq $index }
        
        if ($server) {
            $addresses = ($server.Addresses -join ", ")
            Stop-Server -process $server.Process -description "$($server.Process.ProcessName).exe (PID: $($server.Process.Id), Addresses: $addresses)"
            Write-Host ""
            Write-Host "Press any key to continue..."
            $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null
            continue
        }
        elseif ($index -le ($servers.Count) -and $index -gt 0) {
            # Number is in range but no server found (shouldn't happen)
            Write-Host "Server not found." -ForegroundColor Red
            Start-Sleep -Seconds 2
            continue
        }
        else {
            Write-Host "Number out of range." -ForegroundColor Red
            Start-Sleep -Seconds 2
            continue
        }
    }
    else {
        Write-Host "Invalid input. Please enter a number." -ForegroundColor Red
        Start-Sleep -Seconds 2
        continue
    }
} while ($true)
