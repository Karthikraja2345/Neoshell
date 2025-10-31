#!/usr/bin/env python3
"""
NeoShell - AI-Enhanced Command Line Environment (Universal UI for ps)
"""

import os
import sys
import subprocess
import shlex
import atexit
import glob
import re
from pathlib import Path

# Readline fallback
try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline
    except ImportError:
        readline = None
        print("Warning: readline not found, history and tab completion disabled")

try:
    from rich.console import Console
    from rich.theme import Theme
    from rich.table import Table
    from rich.progress import BarColumn, Progress, TextColumn
    RICH_AVAILABLE = True
    theme = Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "command": "bold cyan",
        "arg": "green",
        "operator": "yellow"
    })
    console = Console(theme=theme)
except ImportError:
    RICH_AVAILABLE = False
    console = None

def print_error(message):
    if RICH_AVAILABLE and console:
        console.print(f"[error]{message}[/error]")
    else:
        print("ERROR:", message)

def print_success(message):
    if RICH_AVAILABLE and console:
        console.print(f"[success]{message}[/success]")
    else:
        print("SUCCESS:", message)

class NeoShell:
    def __init__(self):
        self.running = True
        self.history_file = Path.home() / '.neoshell_history'
        self.setup_history()
        self.setup_completion()
        self.aliases = {}

    def setup_history(self):
        if readline:
            try:
                if self.history_file.exists():
                    readline.read_history_file(str(self.history_file))
                readline.set_history_length(1000)
            except Exception:
                pass
            atexit.register(self.save_history)

    def save_history(self):
        if readline:
            try:
                readline.write_history_file(str(self.history_file))
            except Exception:
                pass

    def setup_completion(self):
        if readline:
            readline.set_completer(self.completer)
            readline.parse_and_bind('tab: complete')
            readline.set_completer_delims(' \t\n')

    def completer(self, text, state):
        if state == 0:
            if '/' in text or text.startswith('~'):
                text_expanded = os.path.expanduser(text)
                self.matches = glob.glob(text_expanded + '*')
                self.matches = [m + '/' if os.path.isdir(m) else m for m in self.matches]
            else:
                self.matches = self.get_commands(text)
        try:
            return self.matches[state]
        except IndexError:
            return None

    def get_commands(self, prefix):
        commands_set = set(['cd', 'pwd', 'exit', 'help', 'history', 'ps', 'clear'])
        commands_set.update([alias for alias in self.aliases.keys() if alias.startswith(prefix)])
        for path_dir in os.environ.get('PATH', '').split(os.pathsep):
            if os.path.isdir(path_dir):
                try:
                    for fname in os.listdir(path_dir):
                        if fname.startswith(prefix):
                            full_path = os.path.join(path_dir, fname)
                            if os.access(full_path, os.X_OK):
                                commands_set.add(fname)
                except PermissionError:
                    pass
        return sorted(commands_set)

    def translate_command_for_windows(self, cmd_dict):
        if sys.platform == 'win32':
            if cmd_dict['command'] == 'ls':
                cmd_dict['command'] = 'cmd'
                cmd_dict['args'] = ['/c', 'dir'] + cmd_dict['args']
            elif cmd_dict['command'] == 'ps':
                cmd_dict['command'] = 'ps'
            elif cmd_dict['command'] == 'grep':
                cmd_dict['command'] = 'findstr'
        return cmd_dict

    def parse_command(self, command_line):
        try:
            tokens = shlex.split(command_line)
        except ValueError as e:
            return {'error': f"Syntax error: {e}"}
        if not tokens:
            return {'error': 'Empty command'}
        cmd_dict = {
            'command': tokens[0],
            'args': tokens[1:],
            'input_file': None,
            'output_file': None,
            'append': False
        }
        return cmd_dict

    def builtin_cd(self, args):
        if not args:
            path = str(Path.home())
        else:
            path = os.path.expanduser(args[0])
        try:
            os.chdir(path)
        except Exception as e:
            print_error(f"cd: {e}")

    def builtin_pwd(self, args):
        print(os.getcwd())

    def builtin_help(self, args):
        print("NeoShell Help: cd, pwd, exit, help, ps. External commands work with Windows translation.")

    def builtin_history(self, args):
        n = int(args[0]) if args and args[0].isdigit() else 20
        if readline:
            length = readline.get_current_history_length()
            start = max(1, length - n + 1)
            for i in range(start, length + 1):
                item = readline.get_history_item(i)
                if item:
                    print(f"{i:4d}  {item}")
        else:
            print("History not available (readline missing)")

    def builtin_ps(self, args):
        """Rich-formatted process table and summary for all platforms."""
        import platform
        if sys.platform == "win32":
            try:
                result = subprocess.run(['tasklist'], capture_output=True, text=True)
                lines = result.stdout.splitlines()
                header_idx = None
                for idx, line in enumerate(lines):
                    if all(x in line for x in ("PID", "Session Name", "Mem Usage")):
                        header_idx = idx
                        break
                if header_idx is None or not RICH_AVAILABLE:
                    print(result.stdout)
                    return
                headers = re.split(r"\s{2,}", lines[header_idx].strip())
                table = Table(title="🔵 Windows Processes", show_lines=True)
                for col in headers:
                    table.add_column(col)
                for line in lines[header_idx+2:]:
                    if not line.strip():
                        continue
                    cells = re.split(r"\s{2,}", line.strip())
                    while len(cells) < len(headers):
                        cells.append('')
                    table.add_row(*cells)
                console.print(table)
                # Print memory summary bar
                import psutil
                mem_info = psutil.virtual_memory()
                cpu_val = psutil.cpu_percent(interval=0.3)
                console.print(f"[bold cyan]🖥️  CPU Usage:[/bold cyan] [yellow]{cpu_val:.1f}%[/yellow]")
                console.print(f"[bold cyan]💾 Memory:[/bold cyan] [blue]{mem_info.percent:.1f}%[/blue] "
                              f"([blue]{mem_info.used // 1024**3}GB[/blue] / [blue]{mem_info.total // 1024**3}GB[/blue])")
                console.print(f"[dim]Platform:[/dim] [green]{platform.platform()}[/green]")
            except Exception as e:
                print_error(f"Error running tasklist: {e}")
        else:
            # Linux/macOS: Full color and details
            try:
                import psutil
                cpu_val = psutil.cpu_percent(interval=0.3)
                mem = psutil.virtual_memory()
                table = Table(title="🟢 Top Processes by CPU Usage", show_lines=True)
                table.add_column("PID", style="cyan", justify="right")
                table.add_column("Name", style="magenta")
                table.add_column("CPU%", style="yellow", justify="right")
                table.add_column("Memory%", style="green", justify="right")
                table.add_column("Status", style="blue")
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                    try:
                        processes.append(proc.info)
                    except Exception:
                        continue
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
                for proc in processes[:10]:
                    table.add_row(
                        str(proc['pid']),
                        proc['name'][:20] if proc['name'] else "",
                        f"{proc['cpu_percent']:.1f}" if proc['cpu_percent'] else "0.0",
                        f"{proc['memory_percent']:.1f}" if proc['memory_percent'] else "0.0",
                        proc['status'] if proc['status'] else ""
                    )
                console.print(table)
                console.print(f"[bold cyan]🖥️  CPU Usage:[/bold cyan] [yellow]{cpu_val:.1f}%[/yellow]")
                console.print(f"[bold cyan]💾 Memory:[/bold cyan] [blue]{mem.percent:.1f}%[/blue] "
                            f"([blue]{mem.used // 1024**3}GB[/blue] / [blue]{mem.total // 1024**3}GB[/blue])")
                console.print(f"[dim]Platform:[/dim] [green]{platform.platform()}[/green]")
            except ImportError:
                os.system("ps aux | head -12")

    def execute_builtin(self, cmd_dict):
        cmd = cmd_dict['command']
        args = cmd_dict['args']

        builtins = {
            'cd': self.builtin_cd,
            'pwd': self.builtin_pwd,
            'exit': lambda x: setattr(self, 'running', False),
            'help': self.builtin_help,
            'history': self.builtin_history,
            'ps': self.builtin_ps
        }

        if cmd in builtins:
            builtins[cmd](args)
            return True
        return False

    def execute_external(self, cmd_dict):
        try:
            cmd_list = [cmd_dict['command']] + cmd_dict['args']
            result = subprocess.run(cmd_list, stderr=subprocess.PIPE, text=True)
            if result.stderr:
                print_error(result.stderr)
        except FileNotFoundError:
            print_error(f"Command not found: {cmd_dict['command']}")
        except PermissionError:
            print_error(f"Permission denied: {cmd_dict['command']}")
        except Exception as e:
            print_error(f"Error: {e}")

    def execute(self, command_line):
        cmd_dict = self.parse_command(command_line)
        if 'error' in cmd_dict:
            print_error(cmd_dict['error'])
            return

        if self.execute_builtin(cmd_dict):
            return

        cmd_dict = self.translate_command_for_windows(cmd_dict)
        if sys.platform == "win32" and cmd_dict['command'] == 'ps':
            self.builtin_ps(cmd_dict['args'])
            return

        self.execute_external(cmd_dict)

    def run(self):
        print("Welcome to NeoShell!")
        print("Type 'help' for commands.\n")
        while self.running:
            try:
                command = input(self.get_prompt()).strip()
                if not command:
                    continue
                self.execute(command)
            except KeyboardInterrupt:
                print("\n(Press Ctrl+D or type 'exit' to quit)")
            except EOFError:
                print("\nGoodbye!")
                break
        print("Goodbye!")

    def get_prompt(self):
        cwd = os.getcwd()
        home = str(Path.home())
        if cwd.startswith(home):
            cwd = '~' + cwd[len(home):]
        user = os.environ.get('USER', 'user')
        try:
            hostname = os.uname().nodename
        except AttributeError:
            hostname = 'host'
        return f"{user}@{hostname} {cwd} $ "

def main():
    shell = NeoShell()
    shell.run()

if __name__ == "__main__":
    main()
