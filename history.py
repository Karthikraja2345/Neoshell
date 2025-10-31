# history.py
"""
Command history and tab completion management
"""

import os
try:
    import readline
except ImportError:
    import pyreadline3 as readline
import atexit
import glob


class Completer:
    """Tab completion provider"""
    
    def __init__(self):
        self.matches = []

    def complete(self, text, state):
        """Completion function for readline"""
        if state == 0:
            if '/' in text or text.startswith('~'):
                # File path completion
                text_expanded = os.path.expanduser(text)
                self.matches = glob.glob(text_expanded + '*')
                self.matches = [m + '/' if os.path.isdir(m) else m for m in self.matches]
            else:
                # Command completion
                self.matches = self._command_completion(text)
        
        try:
            return self.matches[state]
        except IndexError:
            return None

    def _command_completion(self, text):
        """Complete commands from PATH"""
        commands = set()
        
        # Built-in commands
        builtins = ['cd', 'pwd', 'exit', 'help', 'history', 'jobs', 'fg', 'bg',
                   'alias', 'unalias', 'export', 'unset', 'echo', 'ps', 'ai', 'script', 'clear']
        commands.update([cmd for cmd in builtins if cmd.startswith(text)])
        
        # Commands from PATH
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        for directory in path_dirs:
            if os.path.isdir(directory):
                try:
                    for filename in os.listdir(directory):
                        if filename.startswith(text):
                            full_path = os.path.join(directory, filename)
                            if os.access(full_path, os.X_OK):
                                commands.add(filename)
                except PermissionError:
                    continue
        
        return sorted(commands)


def setup_history(history_file=None):
    """Setup readline and load history"""
    if history_file is None:
        history_file = os.path.expanduser('~/.neoshell_history')
    
    readline.parse_and_bind('tab: complete')
    readline.set_history_length(1000)
    
    try:
        if os.path.exists(history_file):
            readline.read_history_file(history_file)
    except IOError:
        pass
    
    atexit.register(lambda: readline.write_history_file(history_file))
    readline.set_completer(Completer().complete)


def show_history(n=20):
    """Show last n commands from history"""
    length = readline.get_current_history_length()
    start = max(1, length - n + 1)
    
    for i in range(start, length + 1):
        item = readline.get_history_item(i)
        if item:
            print(f"{i:4d}  {item}")
