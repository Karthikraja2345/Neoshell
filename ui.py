# ui.py
"""
UI enhancements for NeoShell with fallback support
"""

try:
    from rich.console import Console
    from rich.theme import Theme
    from rich.table import Table
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
    """Print error message"""
    if RICH_AVAILABLE and console:
        console.print(f"[error]✗ {message}[/error]")
    else:
        print(f"ERROR: {message}")


def print_success(message):
    """Print success message"""
    if RICH_AVAILABLE and console:
        console.print(f"[success]✓ {message}[/success]")
    else:
        print(f"SUCCESS: {message}")


def print_info(message):
    """Print info message"""
    if RICH_AVAILABLE and console:
        console.print(f"[info]ℹ {message}[/info]")
    else:
        print(f"INFO: {message}")


def print_warning(message):
    """Print warning message"""
    if RICH_AVAILABLE and console:
        console.print(f"[warning]⚠ {message}[/warning]")
    else:
        print(f"WARNING: {message}")


def print_table(title, headers, rows):
    """Print a formatted table"""
    if RICH_AVAILABLE and console:
        table = Table(title=title)
        for header in headers:
            table.add_column(header)
        for row in rows:
            table.add_row(*row)
        console.print(table)
    else:
        print(f"\n{title}:")
        print(" | ".join(headers))
        print("-" * 60)
        for row in rows:
            print(" | ".join(row))
