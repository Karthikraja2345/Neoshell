# parser.py
"""
Command parser with support for pipes and redirection
"""

import shlex
import subprocess
import sys
from ui import print_error


def parse_command(command_str):
    """Parse command line with I/O redirection"""
    try:
        tokens = shlex.split(command_str)
    except ValueError as e:
        return {'error': f"Syntax error: {e}"}

    if not tokens:
        return {'error': 'Empty command'}

    result = {
        'command': tokens[0],
        'args': [],
        'input_file': None,
        'output_file': None,
        'append': False
    }
    
    i = 1
    while i < len(tokens):
        if tokens[i] == '>':
            if i + 1 < len(tokens):
                result['output_file'] = tokens[i + 1]
                i += 2
            else:
                return {'error': 'Missing filename after >'}
        elif tokens[i] == '>>':
            if i + 1 < len(tokens):
                result['output_file'] = tokens[i + 1]
                result['append'] = True
                i += 2
            else:
                return {'error': 'Missing filename after >>'}
        elif tokens[i] == '<':
            if i + 1 < len(tokens):
                result['input_file'] = tokens[i + 1]
                i += 2
            else:
                return {'error': 'Missing filename after <'}
        else:
            result['args'].append(tokens[i])
            i += 1
    
    return result


def parse_pipeline(command_str):
    """Parse command pipeline separated by |"""
    try:
        pipeline = command_str.split('|')
        commands = []
        
        for cmd in pipeline:
            cmd = cmd.strip()
            if not cmd:
                return {'error': 'Empty command in pipeline'}
            
            parsed = parse_command(cmd)
            if 'error' in parsed:
                return parsed
            commands.append(parsed)
        
        return {'pipeline': commands}
    except Exception as e:
        return {'error': f'Pipeline parsing error: {e}'}


def execute_external(parsed_cmd):
    """Execute external command with I/O redirection"""
    try:
        cmd_list = [parsed_cmd['command']] + parsed_cmd['args']
        
        stdin = None
        stdout = None
        
        if parsed_cmd['input_file']:
            try:
                stdin = open(parsed_cmd['input_file'], 'r')
            except FileNotFoundError:
                print_error(f"Input file not found: {parsed_cmd['input_file']}")
                return
        
        if parsed_cmd['output_file']:
            mode = 'a' if parsed_cmd.get('append', False) else 'w'
            stdout = open(parsed_cmd['output_file'], mode)
        
        result = subprocess.run(
            cmd_list,
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if stdin:
            stdin.close()
        if stdout:
            stdout.close()
        
        if result.stderr:
            print(result.stderr, file=sys.stderr, end='')
        
        return result.returncode
        
    except FileNotFoundError:
        print_error(f"Command not found: {parsed_cmd['command']}")
        return 127
    except PermissionError:
        print_error(f"Permission denied: {parsed_cmd['command']}")
        return 126
    except Exception as e:
        print_error(f"Error: {e}")
        return 1


def execute_pipeline(pipeline):
    """Execute a pipeline of commands"""
    try:
        processes = []
        prev_stdout = None
        
        for i, cmd_dict in enumerate(pipeline):
            cmd_list = [cmd_dict['command']] + cmd_dict['args']
            
            stdin = None
            if i == 0 and cmd_dict['input_file']:
                stdin = open(cmd_dict['input_file'], 'r')
            elif prev_stdout:
                stdin = prev_stdout
            
            stdout = None
            if i == len(pipeline) - 1:
                if cmd_dict['output_file']:
                    mode = 'a' if cmd_dict.get('append', False) else 'w'
                    stdout = open(cmd_dict['output_file'], mode)
            else:
                stdout = subprocess.PIPE
            
            proc = subprocess.Popen(
                cmd_list,
                stdin=stdin,
                stdout=stdout,
                stderr=subprocess.PIPE,
                text=True
            )
            
            processes.append(proc)
            
            if prev_stdout:
                prev_stdout.close()
            
            prev_stdout = proc.stdout
        
        for proc in processes:
            proc.wait()
            if proc.stderr:
                err = proc.stderr.read()
                if err:
                    print(err, file=sys.stderr, end='')
        
        return 0
        
    except FileNotFoundError:
        print_error("Command not found in pipeline")
        return 127
    except Exception as e:
        print_error(f"Pipeline error: {e}")
        return 1
