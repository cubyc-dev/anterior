import logging
import sys

from rich.console import Console
from rich.logging import RichHandler

logger: logging.Logger = logging.getLogger('anterior')
console = Console(file=sys.stdout, force_terminal=True)
logger.addHandler(RichHandler(tracebacks_show_locals=True, console=console))