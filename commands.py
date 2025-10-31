# commands.py
"""
Built-in commands for NeoShell
"""

import os
import sys
import subprocess
from ui import print_error, print_success, print_info, print_warning, print_table, RICH_AVAILABLE

try:
    from rich.table import Table
    from rich.console import Console as RichConsole
    RICH_AVAILABLE = True
    console = RichConsole()
except ImportError:
    RICH_AVAILABLE = False


def cd(path):
    """Change directory"""
    try:
        if not path:
            path = os.path.expanduser('~')
        else:
            path = os.path.expandvars(os.path.expanduser(path))
        os.chdir(path)
    except FileNotFoundError:
        print_error(f"cd: {path}: No such file or directory")
    except PermissionError:
        print_error(f"cd: {path}: Permission denied")
    except Exception as e:
        print_error(f"cd: {e}")


def pwd():
    """Print working directory"""
    print(os.getcwd())


def help_command():
    """Display comprehensive help"""
    help_text = """
╔════════════════════════════════════════════════════════════════════╗
║         NeoShell - AI-Enhanced Command Line Environment            ║
╚════════════════════════════════════════════════════════════════════╝

BUILT-IN COMMANDS:
  cd [dir]         - Change directory (cd ~ for home)
  pwd              - Print working directory
  exit             - Exit the shell
  help             - Show this help message
  history [n]      - Show last n commands
  jobs             - List background jobs
  fg <job_id>      - Bring job to foreground
  bg <job_id>      - Resume job in background
  alias [n=v]      - Create or show aliases
  unalias <name>   - Remove alias
  export [VAR=v]   - Set environment variable
  unset <VAR>      - Remove environment variable
  echo [args]      - Print text (supports $VAR)
  ps               - Show process information
  ai <query>       - Get AI command suggestions
  script <file>    - Run shell script
  clear            - Clear screen

FEATURES:
  ✓ Piping              : command1 | command2 | command3
  ✓ I/O Redirection     : > (write), >> (append), < (read)
  ✓ Background Jobs     : command &
  ✓ Aliases             : alias ll='ls -la'
  ✓ Environment Vars    : export VAR=value; echo $VAR
  ✓ Tab Completion      : Press TAB
  ✓ Command History     : Press UP/DOWN arrows
  ✓ Git Branch Prompt   : Shows current git branch
  ✓ Process Monitoring  : View CPU/memory usage
  ✓ Shell Scripting     : Run .sh script files

SHORTCUTS:
  TAB              - Auto-complete commands/files
  UP/DOWN arrows   - Navigate command history
  Ctrl+C           - Cancel current input
  Ctrl+D or exit   - Quit shell

EXAMPLES:
  ls -la | grep .py          # Pipe: list and filter
  ls > files.txt             # Redirect to file
  cat < input.txt > out.txt  # Read from and write to files
  sleep 30 &                 # Run in background
  fg 1                       # Bring job 1 to foreground
  alias ll='ls -la'          # Create alias
  export PATH=$PATH:/usr/local/bin  # Modify PATH
  ps                         # Show process info
  script myscript.sh         # Run script file
  ai "list files"            # Get AI suggestion
"""
    print(help_text)


def export_var(args):
    """Set environment variable"""
    if not args:
        # Show all environment variables
        if RICH_AVAILABLE:
            table = Table(title="Environment Variables")
            table.add_column("Variable", style="cyan")
            table.add_column("Value", style="white")
            for key, value in sorted(os.environ.items()):
                display_value = value[:50] + "..." if len(value) > 50 else value
                table.add_row(key, display_value)
            console.print(table)
        else:
            for key, value in os.environ.items():
                print(f"{key}={value}")
        return
    
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            os.environ[key] = value
            print_success(f"Exported: {key}={value}")
        else:
            print_error(f"export: invalid syntax: {arg}")


def unset_var(args):
    """Unset environment variable"""
    if not args:
        print_error("unset: variable name required")
        return
    
    for var in args:
        if var in os.environ:
            del os.environ[var]
            print_success(f"Unset: {var}")
        else:
            print_warning(f"unset: {var}: not found")


def echo_command(args):
    """Echo command with variable expansion"""
    output = []
    for arg in args:
        if arg.startswith('$'):
            var_name = arg[1:]
            output.append(os.environ.get(var_name, ''))
        else:
            output.append(arg)
    print(' '.join(output))


def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')
