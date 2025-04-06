# Script to get Windows 11 desktop names with debugging

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient

# Create a log file for debugging
$logPath = "$PSScriptRoot\desktop_script_log.txt"
"Script started at $(Get-Date)" | Out-File -FilePath $logPath -Force

function Write-Log {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $message" | Out-File -FilePath $logPath -Append
    Write-Host $message
}

try {
    Write-Log "Opening Task View..."
    
    # Send Windows+Tab to open Task View
    [System.Windows.Forms.SendKeys]::SendWait("^{ESC}")
    Start-Sleep -Milliseconds 100
    [System.Windows.Forms.SendKeys]::SendWait("%{TAB}")
    Start-Sleep -Milliseconds 1000  # Longer wait to ensure Task View opens
    
    Write-Log "Getting automation elements..."
    
    # Get the root automation element
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    Write-Log "Root element obtained"
    
    # Try to find the Task View container
    $desktopNames = @()
    
    # Look for elements with specific automation IDs that might contain desktop names
    $allElements = $root.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants, 
        [System.Windows.Automation.Condition]::TrueCondition
    )
    
    Write-Log "Found $($allElements.Count) total UI elements"
    
    # Look for desktop-related elements
    foreach ($element in $allElements) {
        if ($element.Current.LocalizedControlType -eq "button" -or 
            $element.Current.ClassName -eq "ThumbnailButton" -or
            $element.Current.Name -match "Desktop") {
            
            Write-Log "Found potential desktop element: $($element.Current.Name) (Type: $($element.Current.LocalizedControlType), Class: $($element.Current.ClassName))"
            
            if ($element.Current.Name -match "Desktop" -or $element.Current.Name -ne "") {
                $desktopNames += $element.Current.Name
            }
        }
    }
    
    # Close Task View
    [System.Windows.Forms.SendKeys]::SendWait("{ESC}")
    Write-Log "Task View closed"
    
    # Remove duplicates
    $uniqueNames = $desktopNames | Select-Object -Unique
    Write-Log "Found $($uniqueNames.Count) unique desktop names"
    
    # Output path for desktop names
    $outputPath = "$PSScriptRoot\desktop_names.txt"
    
    if ($uniqueNames.Count -gt 0) {
        # Write names to file
        $uniqueNames | Out-File -FilePath $outputPath -Force
        Write-Log "Desktop names saved to: $outputPath"
    } else {
        # Fallback to registry method
        Write-Log "No desktop names found via UI, falling back to registry method"
        
        $regPath = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops"
        $desktopIDs = (Get-ItemProperty -Path $regPath -Name "VirtualDesktopIDs" -ErrorAction SilentlyContinue).VirtualDesktopIDs
        
        # Calculate number of desktops
        $desktopCount = if ($desktopIDs) { $desktopIDs.Length / 16 } else { 1 }
        Write-Log "Found $desktopCount desktops via registry"
        
        # Generate desktop names
        "" | Out-File -FilePath $outputPath -Force
        for ($i = 1; $i -le $desktopCount; $i++) {
            "Desktop $i" | Out-File -FilePath $outputPath -Append
        }
        
        Write-Log "Generated generic desktop names"
    }
    
    Write-Log "Script completed successfully"
} catch {
    $errorMessage = $_.Exception.Message
    Write-Log "ERROR: $errorMessage"
    Write-Log "Stack Trace: $($_.Exception.StackTrace)"
    
    # Create a basic fallback file
    "Desktop 1" | Out-File -FilePath "$PSScriptRoot\desktop_names.txt" -Force
    Write-Log "Created fallback desktop list"
}

Write-Log "Script finished at $(Get-Date)"
Write-Host "Script completed. Check desktop_names.txt for results and desktop_script_log.txt for details." 