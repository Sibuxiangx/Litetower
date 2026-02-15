"""Litetower 日志系统"""

from __future__ import annotations

import logging
import sys
import types
from datetime import datetime
from logging import LogRecord
from types import TracebackType
from typing import Any, Callable, Dict, Iterable, List, Optional, Type, Union

from loguru import logger as loguru_logger
from loguru._logger import Core
from rich.console import Console, ConsoleRenderable
from rich.logging import RichHandler
from rich.text import Text
from rich.theme import Theme

# Map standard logging levels to Loguru levels
try:
    for lv in Core().levels.values():
        logging.addLevelName(lv.no, lv.name)
except Exception:
    pass

# Global Console
console = Console(
    stderr=True,
    theme=Theme(
        {
            "logging.level.success": "bold green",
            "logging.level.trace": "bright_black",
            "logging.level.info": "bold green",
            "logging.level.warning": "bold yellow",
            "logging.level.error": "bold red",
            "logging.level.critical": "bold red reverse",
        }
    )
)


class LoguruHandler(logging.Handler):
    """Intercept standard logging messages and emit to Loguru."""
    
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def highlight(style: str) -> Dict[str, Callable[[Text], Text]]:
    """Add `style` to RichHandler's log text."""

    def highlighter(text: Text) -> Text:
        return Text(text.plain, style=style)

    return {"highlighter": highlighter}


def _get_module_tag(name: str) -> Text:
    """Map raw module names to colorful tags."""
    name = name or ""
    tag = "System"
    style = "blue"
    
    if name.startswith("litetower.app") or name == "litetower":
        tag = "Bot"
        style = "bold cyan"
    elif name.startswith("litetower.services.auth"):
        tag = "Auth"
        style = "bold magenta"
    elif name.startswith("litetower.network.qqapi"):
        tag = "QQAPI"
        style = "bold blue"
    elif name.startswith("litetower.network.webhook"):
        tag = "Webhook"
        style = "bold blue"
    elif name.startswith("litetower.events"):
        tag = "Event"
        style = "yellow"
    elif name.startswith("litetower.message"):
        tag = "Matcher"
    elif name.startswith("litetower.services"):
        tag = "Service"
    elif name.startswith("launart"):
        tag = "Launart"
    elif name.startswith("uvicorn"):
        tag = "Uvicorn"
        style = "green"
    elif name.startswith("httpx"):
        tag = "HTTPX"
    
    return Text(f"[{tag}]", style=style)


class LoguruRichHandler(RichHandler):
    """
    Custom RichHandler to replicate [Time] [Level] [Tag] Message style
    while keeping Rich's highlighting and traceback power.
    """

    def render_message(self, record: LogRecord, message: str) -> "ConsoleRenderable":
        # 1. Format Time: [YYYY-MM-DD HH:mm:ss] (Cyan)
        # Note: We manually format here to ensure it's always present and styled correctly
        log_time = datetime.fromtimestamp(record.created)
        time_str = log_time.strftime("%Y-%m-%d %H:%M:%S")
        time_text = Text(f"[{time_str}]", style="cyan")

        # 2. Format Level: [LEVEL] (Color determined by logging level)
        # Map standard levels to user requested display names if needed
        level_name = record.levelname
        level_map = {
            "WARNING": "WARN",
            "CRITICAL": "FATAL", 
        }
        display_level = level_map.get(level_name, level_name)
        
        # Get color from theme or default map
        level_style = f"logging.level.{level_name.lower()}"
        # Fallback colors if theme doesn't match exactly (though we set theme below)
        
        level_text = Text(f"[{display_level}]", style=level_style)
        
        # 3. Format Tag: [Tag] (Blue)
        tag_text = _get_module_tag(record.name)

        # 4. Handle Message (User's message with rich markup if enabled)
        # Add extra attrs handling from richuru
        extra: dict = getattr(record, "extra", {})
        if "rich" in extra:
            msg_content = extra["rich"]
        elif "style" in extra:
            record.__dict__.update(highlight(extra["style"]))
            msg_content = super().render_message(record, message)
        else:
            msg_content = super().render_message(record, message)
        
        # 5. Assemble: [Time] [Level] [Tag] Message
        # We assume msg_content is a ConsoleRenderable (likely Text or similar)
        
        final_output = Text()
        final_output.append(time_text)
        final_output.append(" ")
        final_output.append(level_text)
        final_output.append(" ")
        final_output.append(tag_text)
        final_output.append(" ")
        
        if isinstance(msg_content, Text):
            final_output.append(msg_content)
        else:
            # If msg_content is a Group or other Renderable (e.g. traceback)
            # We print our prefix then the content on next line? 
            # Or try to console.render?
            # For tracebacks, RichHandler returns a Group(message_text, traceback).
            # We should try to extract message text if possible, or just append the whole thing.
            # But appending a Group to Text isn't valid.
            
            # Use Rich's Table or Group to layout.
            from rich.console import Group
            return Group(final_output, msg_content)

        return final_output


ExceptionHook = Callable[[Type[BaseException], BaseException, Optional[TracebackType]], Any]


def _loguru_exc_hook(typ: Type[BaseException], val: BaseException, tb: Optional[TracebackType]):
    loguru_logger.opt(exception=(typ, val, tb)).error("Exception:")


def setup_logging(
    level: str = "INFO",
    exc_hook: Optional[ExceptionHook] = _loguru_exc_hook,
) -> Any:
    """Configure logging system"""
    loguru_logger.remove()
    
    # Intercept standard logging
    logging.basicConfig(handlers=[LoguruHandler()], level=0, force=True)
    
    # Configure Loguru to use RichHandler
    # We disable built-in columns (time, level) to handle them manually in render_message
    loguru_logger.add(
        LoguruRichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_time=False,   # Manual handling
            show_level=False,  # Manual handling
            show_path=False,   # Manual handling
            enable_link_path=False,
            markup=True,
        ),
        format="{message}",
        level=level,
        enqueue=True,
    )
    
    if exc_hook is not None:
        sys.excepthook = exc_hook
        
    return loguru_logger


logger = loguru_logger
setup_logging()


def set_level(level: str) -> None:
    setup_logging(level)


def enable_debug() -> None:
    set_level("DEBUG")


def banner() -> None:
    """Print requested banner style"""
    width = 40
    border_color = "magenta"
    text_color = "bold cyan"
    
    top = f"[{border_color}]╔{'═' * (width-2)}╗[/{border_color}]"
    mid_empty = f"[{border_color}]║{' ' * (width-2)}║[/{border_color}]"
    
    title = "⚡  Litetower (QQBot)"
    
    content_line = f"[{border_color}]║[/{border_color}]{' ' * 9}[{text_color}]{title}[/{text_color}]{' ' * 8}[{border_color}]║[/{border_color}]"
    
    bot = f"[{border_color}]╚{'═' * (width-2)}╝[/{border_color}]"
    
    console.print(top)
    console.print(mid_empty)
    console.print(content_line)
    console.print(mid_empty)
    console.print(bot)


# Helper Functions
# ──────────────────────────────────────────

def log_event_flow(event_type: str, source: str, detail: str) -> None:
    """Log an incoming event flow"""
    # [Event] GroupMessage from Group(123) -> Dispatching
    # Use Rich markup in message
    msg = f"[bold yellow]{event_type}[/] from [blue]{source}[/] -> {detail}"
    logger.bind(name="litetower.events").info(msg)


def log_message_send(target_type: str, target_id: str, message_id: str) -> None:
    """Log an outgoing message"""
    msg = (
        f"Send Message -> [cyan]{target_type}({target_id})[/cyan] | ID: [magenta]{message_id}[/magenta]"
    )
    logger.bind(name="litetower.network.qqapi").info(msg)


def log_recall(target_type: str, target_id: str, message_id: str, success: bool) -> None:
    """Log a recall action"""
    status = "[green]Success[/green]" if success else "[red]Failed[/red]"
    msg = (
        f"Recall Message ({status}) -> [cyan]{target_type}({target_id})[/cyan] | ID: [magenta]{message_id}[/magenta]"
    )
    if success:
        logger.bind(name="litetower.network.qqapi").info(msg)
    else:
        logger.bind(name="litetower.network.qqapi").error(msg)
