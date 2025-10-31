#!/bin/bash
# Example shell script for NeoShell

echo "=== NeoShell Example Script ==="
echo "Current Directory:"
pwd
echo ""
echo "User Information:"
echo "User: $USER"
echo "Home: $HOME"
echo ""
echo "Directory Contents:"
ls -la | head -10
echo ""
echo "System Information:"
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo ""
echo "=== Script Completed ==="
