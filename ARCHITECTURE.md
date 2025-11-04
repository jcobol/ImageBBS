# ImageBBS Python Port - Architecture Document

This document describes the architecture for the Python port of ImageBBS v2, designed to recreate the Commodore 64 BBS experience while running on modern platforms.

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [Project Structure](#project-structure)
4. [Core Architecture](#core-architecture)
5. [Module Specifications](#module-specifications)
6. [Data Layer](#data-layer)
7. [Protocol & I/O Layer](#protocol--io-layer)
8. [Command System](#command-system)
9. [Session Management](#session-management)
10. [Extension System](#extension-system)
11. [Configuration](#configuration)
12. [Testing Strategy](#testing-strategy)

---

## Overview

### Goals

- **Authentic Experience**: Recreate the look and feel of ImageBBS v2 on C64
- **Portability**: Run anywhere Python runs (Linux, Windows, macOS)
- **Maintainability**: Clean, modular Python code with good separation of concerns
- **Extensibility**: Support the original plus-file extension system
- **Compatibility**: Import existing v2 user databases and message bases

### Technology Stack

- **Python 3.10+**: Core language
- **asyncio**: Async I/O for telnet connections
- **telnetlib3** or **asynctelnet**: Telnet protocol handling
- **structlog**: Structured logging
- **pydantic**: Data validation and settings
- **pytest**: Testing framework

---

## Design Principles

### 1. Layer Separation

```
┌─────────────────────────────────────┐
│     Command Layer (BBS Logic)       │  ← User commands, menus
├─────────────────────────────────────┤
│    Session Layer (State Mgmt)       │  ← User session, context
├─────────────────────────────────────┤
│   Terminal Layer (I/O Formatting)   │  ← PETSCII/ANSI translation
├─────────────────────────────────────┤
│  Protocol Layer (Telnet/Serial)     │  ← Network I/O
├─────────────────────────────────────┤
│     Data Layer (Storage)             │  ← Files, users, messages
└─────────────────────────────────────┘
```

### 2. Assembly Command Abstraction

Map C64 assembly calls (& commands) to Python methods:

```python
# C64: &,52,4,3  (check local mode flag)
session.flags.check(Flag.LOCAL_MODE)

# C64: &,1  (inline text output)
session.output.inline()

# C64: &,60,2,0,array(),"filename",device  (load struct)
storage.struct.load(filename, array_type)
```

### 3. Character Encoding Pipeline

```
User Input → Protocol Layer → Encoding Layer → Application Layer
   ANSI    →    Telnet      →   PETSCII     →   BBS Logic
```

### 4. Async I/O Throughout

All I/O operations use async/await to support multiple concurrent users.

---

## Project Structure

```
src/imagebbs/
├── __init__.py
├── __main__.py              # Entry point: python -m imagebbs
│
├── core/                    # Core BBS engine
│   ├── __init__.py
│   ├── bbs.py              # Main BBS class
│   ├── session.py          # User session management
│   ├── context.py          # Session context (state)
│   └── events.py           # Event system (login, logout, etc)
│
├── terminal/               # Terminal I/O & encoding
│   ├── __init__.py
│   ├── base.py            # Base terminal interface
│   ├── petscii.py         # PETSCII encoding/decoding
│   ├── ansi.py            # ANSI color translation
│   ├── ascii_mode.py      # ASCII translation
│   ├── ibm_graphics.py    # IBM graphics characters
│   └── output.py          # Output formatting & MCI
│
├── protocol/              # Network protocol handlers
│   ├── __init__.py
│   ├── telnet.py          # Telnet server
│   ├── serial.py          # Serial port support (optional)
│   └── xmodem.py          # XMODEM protocol
│
├── data/                  # Data storage layer
│   ├── __init__.py
│   ├── base.py           # Base storage interface
│   ├── files.py          # File I/O abstraction
│   ├── sequential.py     # Sequential file handler
│   ├── relative.py       # Relative (random access) file handler
│   └── struct.py         # Struct file format handler
│
├── models/                # Data models
│   ├── __init__.py
│   ├── user.py           # User account model
│   ├── message.py        # Message/post model
│   ├── email.py          # Email model
│   ├── file_entry.py     # File library entry model
│   ├── feedback.py       # Feedback model
│   └── config.py         # System configuration model
│
├── commands/              # Command implementations
│   ├── __init__.py
│   ├── base.py           # Base command class
│   ├── registry.py       # Command registry
│   ├── parser.py         # Command parser
│   │
│   ├── general.py        # General commands (?, T, ST, etc)
│   ├── messaging.py      # SB (sub-boards) commands
│   ├── email.py          # EM (email) commands
│   ├── files.py          # U/D section commands
│   ├── user.py           # User commands (UL, EP, etc)
│   ├── local.py          # Local/maintenance commands
│   └── system.py         # System commands (O, Q, etc)
│
├── subsystems/            # Major BBS subsystems
│   ├── __init__.py
│   ├── messages.py       # Message base system
│   ├── email.py          # Email system
│   ├── files.py          # File library system
│   ├── feedback.py       # Feedback system
│   ├── voting.py         # Voting booth
│   └── sayings.py        # Sayings system
│
├── system/                # System management
│   ├── __init__.py
│   ├── lightbar.py       # Lightbar flag system
│   ├── flags.py          # User flags
│   ├── access.py         # Access level system
│   ├── statistics.py     # BAR (Board Activity Register)
│   ├── logging.py        # Activity logging
│   └── maintenance.py    # Auto-maintenance
│
├── editor/                # Text editor
│   ├── __init__.py
│   ├── line_editor.py    # Line-based editor
│   ├── visual_editor.py  # Visual (full-screen) editor
│   └── mci.py            # MCI (Message Command Interpreter)
│
├── extensions/            # Plus-file extension system
│   ├── __init__.py
│   ├── loader.py         # Dynamic module loader
│   ├── ecs.py            # ECS (Extended Command Set)
│   └── modules/          # Plus-file implementations
│       ├── __init__.py
│       ├── lo.py         # Login/logoff modules
│       ├── gf.py         # General Files modules
│       └── ...           # Other plus-modules
│
├── network/               # Network features
│   ├── __init__.py
│   ├── netmail.py        # NetMail system
│   └── nodes.py          # Multi-node support
│
├── config/                # Configuration
│   ├── __init__.py
│   ├── settings.py       # Application settings
│   └── defaults.py       # Default configuration
│
└── utils/                 # Utility functions
    ├── __init__.py
    ├── time.py           # Time/date utilities
    ├── formatting.py     # String formatting
    ├── validation.py     # Input validation
    └── conversion.py     # Data type conversions
```

---

## Core Architecture

### BBS Class (core/bbs.py)

The main BBS server instance.

```python
from typing import Dict, Optional
import asyncio
from .session import Session
from ..protocol.telnet import TelnetServer
from ..data.base import Storage
from ..system.lightbar import LightbarSystem

class ImageBBS:
    """Main BBS server instance."""

    def __init__(self, config: BBSConfig):
        self.config = config
        self.storage = Storage(config.data_path)
        self.lightbar = LightbarSystem(self.storage)
        self.sessions: Dict[str, Session] = {}
        self.statistics = Statistics(self.storage)

    async def start(self):
        """Start the BBS server."""
        # Initialize subsystems
        await self.storage.initialize()
        await self.lightbar.load_defaults()

        # Start telnet server
        server = TelnetServer(self.config.telnet_port, self.handle_connection)
        await server.start()

        # Start maintenance tasks
        asyncio.create_task(self.maintenance_loop())

    async def handle_connection(self, reader, writer):
        """Handle new incoming connection."""
        session = Session(self, reader, writer)
        try:
            await session.run()
        finally:
            await session.cleanup()

    async def maintenance_loop(self):
        """Background maintenance tasks."""
        while True:
            await asyncio.sleep(3600)  # Every hour
            await self.statistics.update()
            # Auto-maintenance at configured time
            if self.should_run_automaint():
                await self.run_automaint()
```

### Session Class (core/session.py)

Represents a single user connection and session state.

```python
from dataclasses import dataclass
from typing import Optional
from ..models.user import User
from ..terminal.base import Terminal
from ..commands.registry import CommandRegistry

@dataclass
class SessionContext:
    """Current session state."""
    user: Optional[User] = None
    access_level: int = 0
    time_remaining: int = 0
    expert_mode: bool = False
    current_subsystem: Optional[str] = None
    current_area: Optional[int] = None
    command_history: list[str] = None

    def __post_init__(self):
        if self.command_history is None:
            self.command_history = []

class Session:
    """User session handler."""

    def __init__(self, bbs: ImageBBS, reader, writer):
        self.bbs = bbs
        self.reader = reader
        self.writer = writer
        self.context = SessionContext()
        self.terminal = Terminal(self)
        self.commands = CommandRegistry()
        self.flags = UserFlags()

    async def run(self):
        """Main session loop."""
        try:
            # Login sequence
            if not await self.handle_login():
                return

            # Main command loop
            while not self.context.logged_off:
                # Check time remaining
                if self.context.time_remaining <= 0:
                    await self.terminal.output("Time's up!\n")
                    break

                # Get command
                prompt = self.get_prompt()
                command = await self.terminal.input_line(prompt)

                # Execute command
                await self.execute_command(command)

        except ConnectionLost:
            await self.log_carrier_drop()
        finally:
            await self.handle_logoff()

    async def handle_login(self) -> bool:
        """Handle user login."""
        # Display welcome screen
        await self.terminal.output_file("s.welcome")

        # Get handle
        handle = await self.terminal.input_line("Handle: ")
        if not handle:
            return False

        # Load user or create new
        user = await self.bbs.storage.users.find(handle)
        if user:
            # Existing user - verify password
            password = await self.terminal.input_password("Password: ")
            if not user.verify_password(password):
                await self.terminal.output("Incorrect password.\n")
                return False
        else:
            # New user signup
            if not self.bbs.lightbar.check(Flag.NEW_USERS_ALLOWED):
                await self.terminal.output("New users not allowed.\n")
                return False
            user = await self.handle_new_user(handle)
            if not user:
                return False

        # Set up session
        self.context.user = user
        self.context.access_level = user.access_level
        self.context.time_remaining = await self.calculate_time_limit()

        # Update user stats
        user.last_call = datetime.now()
        user.total_calls += 1
        user.calls_today += 1
        await self.bbs.storage.users.save(user)

        # Log login
        await self.bbs.statistics.log_login(user)

        return True

    async def execute_command(self, command_str: str):
        """Parse and execute a command."""
        # Command stacking support (commands separated by ;)
        commands = command_str.split(';')

        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue

            # Check for ECS command
            if await self.try_execute_ecs(cmd):
                continue

            # Standard command
            command = self.commands.parse(cmd)
            if command:
                await command.execute(self)
            else:
                await self.terminal.output(f"Unknown command: {cmd}\n")

    async def calculate_time_limit(self) -> int:
        """Calculate time limit based on access level, prime time, etc."""
        # Base time by access level
        base_time = self.bbs.config.time_limits[self.context.access_level]

        # Prime time reduction
        if self.bbs.lightbar.check(Flag.PRIME_TIME):
            base_time = min(base_time, self.bbs.config.prime_time_limit)

        return base_time
```

---

## Module Specifications

### Terminal Layer

#### Terminal Base Class (terminal/base.py)

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

class TerminalMode(Enum):
    """Terminal modes matching v2 file-formats.txt."""
    CBM_CG = 1        # PETSCII graphics
    ASCII = 2         # Plain ASCII
    ASCII_IBM = 3     # ASCII + IBM graphics
    ASCII_ANSI = 4    # ASCII + ANSI color
    ANSI_CG = 5       # ANSI with graphics

class Terminal:
    """Terminal I/O handler with encoding support."""

    def __init__(self, session: 'Session'):
        self.session = session
        self.mode = TerminalMode.ASCII
        self.width = 40
        self.height = 24
        self.linefeeds = False
        self.more_prompt = True
        self.lines_output = 0

    async def output(self, text: str):
        """Output text with encoding translation."""
        # Apply MCI substitutions if enabled
        if self.session.flags.check(Flag.MCI_ENABLED):
            text = self.apply_mci(text)

        # Translate to appropriate encoding
        encoded = self.encode(text)

        # Send to client
        self.session.writer.write(encoded)
        await self.session.writer.drain()

        # Track lines for more prompt
        self.lines_output += text.count('\n')
        if self.more_prompt and self.lines_output >= self.height - 1:
            await self.show_more_prompt()

    def encode(self, text: str) -> bytes:
        """Encode text based on terminal mode."""
        if self.mode == TerminalMode.CBM_CG:
            return petscii_encode(text)
        elif self.mode == TerminalMode.ASCII:
            return text.encode('ascii', errors='replace')
        elif self.mode == TerminalMode.ASCII_IBM:
            return ibm_encode(text)
        elif self.mode == TerminalMode.ASCII_ANSI:
            return ansi_encode(text)
        elif self.mode == TerminalMode.ANSI_CG:
            return ansi_encode(text, graphics=True)

    async def input_line(self, prompt: str = "") -> str:
        """Input a line of text with editing."""
        if prompt:
            await self.output(prompt)

        line = []
        while True:
            char = await self.get_char()

            if char == '\r' or char == '\n':
                await self.output('\r\n')
                return ''.join(line)
            elif char == '\x08' or char == '\x7f':  # Backspace/DEL
                if line:
                    line.pop()
                    await self.output('\x08 \x08')
            elif char == '\x03':  # Ctrl-C
                raise UserAbort()
            elif char.isprintable():
                line.append(char)
                await self.output(char)

    async def input_password(self, prompt: str = "Password: ") -> str:
        """Input password (no echo)."""
        await self.output(prompt)
        password = []
        while True:
            char = await self.get_char()
            if char == '\r' or char == '\n':
                await self.output('\r\n')
                return ''.join(password)
            elif char == '\x08' or char == '\x7f':
                if password:
                    password.pop()
            elif char.isprintable():
                password.append(char)

    async def output_file(self, filename: str, variables: dict = None):
        """Output a text file with MCI substitution."""
        content = await self.session.bbs.storage.read_text_file(filename)
        if variables:
            content = self.substitute_variables(content, variables)
        await self.output(content)

    async def show_more_prompt(self):
        """Show 'More? [Y/n/=]' prompt."""
        response = await self.input_line("More? [Y/n/=] ")
        self.lines_output = 0

        if response.lower() == 'n':
            raise AbortOutput()
        elif response == '=':
            self.more_prompt = False
```

#### PETSCII Encoding (terminal/petscii.py)

```python
"""PETSCII encoding/decoding support."""

# PETSCII to Unicode mapping
PETSCII_TO_UNICODE = {
    0x00: '\u0000',  # Null
    0x05: '\u2588',  # Solid block
    0x12: '\u2571',  # Diagonal /
    0x13: '\u2572',  # Home
    # ... complete mapping
    0xa0: ' ',       # Shift-space
    0xc1: 'A',       # Uppercase A in lowercase mode
    # ... complete mapping
}

UNICODE_TO_PETSCII = {v: k for k, v in PETSCII_TO_UNICODE.items()}

def petscii_to_unicode(petscii_bytes: bytes) -> str:
    """Convert PETSCII bytes to Unicode string."""
    result = []
    for byte in petscii_bytes:
        result.append(PETSCII_TO_UNICODE.get(byte, '?'))
    return ''.join(result)

def unicode_to_petscii(text: str) -> bytes:
    """Convert Unicode string to PETSCII bytes."""
    result = bytearray()
    for char in text:
        petscii = UNICODE_TO_PETSCII.get(char, 0x3f)  # ? as default
        result.append(petscii)
    return bytes(result)

# Color codes
class PETSCIIColor:
    BLACK = 0x90
    WHITE = 0x05
    RED = 0x1c
    CYAN = 0x9f
    PURPLE = 0x9c
    GREEN = 0x1e
    BLUE = 0x1f
    YELLOW = 0x9e
    ORANGE = 0x81
    BROWN = 0x95
    LIGHT_RED = 0x96
    DARK_GRAY = 0x97
    GRAY = 0x98
    LIGHT_GREEN = 0x99
    LIGHT_BLUE = 0x9a
    LIGHT_GRAY = 0x9b
```

#### ANSI Translation (terminal/ansi.py)

```python
"""ANSI color code translation."""

# C64 to ANSI color mapping
C64_TO_ANSI = {
    'black': '\x1b[30m',
    'white': '\x1b[37m',
    'red': '\x1b[31m',
    'cyan': '\x1b[36m',
    'purple': '\x1b[35m',
    'green': '\x1b[32m',
    'blue': '\x1b[34m',
    'yellow': '\x1b[33m',
    # ... complete mapping
}

def petscii_color_to_ansi(petscii_code: int) -> str:
    """Convert PETSCII color code to ANSI escape sequence."""
    color_map = {
        0x05: '\x1b[37m',  # White
        0x1c: '\x1b[31m',  # Red
        0x1e: '\x1b[32m',  # Green
        0x1f: '\x1b[34m',  # Blue
        0x81: '\x1b[33m',  # Orange/Yellow
        0x90: '\x1b[30m',  # Black
        0x9c: '\x1b[35m',  # Purple
        0x9e: '\x1b[33m',  # Yellow
        0x9f: '\x1b[36m',  # Cyan
        # ... complete mapping
    }
    return color_map.get(petscii_code, '')

def ansi_encode(text: str, graphics: bool = False) -> bytes:
    """Encode text with ANSI color codes."""
    # Replace C64 color markers with ANSI
    # Handle {color} markers from MCI
    # Return encoded bytes
    pass
```

---

## Data Layer

### Storage Base (data/base.py)

```python
from pathlib import Path
from typing import Optional, List
from ..models.user import User

class Storage:
    """Main storage interface."""

    def __init__(self, data_path: Path):
        self.data_path = Path(data_path)
        self.users = UserStorage(self.data_path / "users")
        self.messages = MessageStorage(self.data_path / "messages")
        self.email = EmailStorage(self.data_path / "email")
        self.files = FileStorage(self.data_path / "files")
        self.system = SystemStorage(self.data_path / "system")

    async def initialize(self):
        """Initialize storage subsystems."""
        self.data_path.mkdir(parents=True, exist_ok=True)
        await self.users.initialize()
        await self.messages.initialize()
        await self.email.initialize()
        await self.files.initialize()
        await self.system.initialize()

class UserStorage:
    """User account storage."""

    def __init__(self, path: Path):
        self.path = path
        self.config_file = path / "u.config"
        self.index_file = path / "u.index"

    async def initialize(self):
        """Initialize user storage."""
        self.path.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            await self.create_default_users()

    async def find(self, handle: str) -> Optional[User]:
        """Find user by handle."""
        # Search u.index for handle
        # Load user record from u.config
        pass

    async def save(self, user: User):
        """Save user record."""
        # Update u.config and u.index
        pass

    async def list_users(self, access_filter: int = 0) -> List[User]:
        """List all users with optional access level filter."""
        pass
```

### Struct File Format (data/struct.py)

```python
from typing import List, Dict, Any, Type
from dataclasses import dataclass
import struct

@dataclass
class StructField:
    """Field definition in a struct."""
    name: str
    offset: int
    length: int
    type: str  # 'string', 'int', 'date', 'flags'

class StructFile:
    """
    Handle v2 struct file format.

    Struct files are binary files with fixed-size records containing
    multiple fields. Used for messages, email, file lists, etc.
    """

    def __init__(self, filename: str, record_size: int, fields: List[StructField]):
        self.filename = filename
        self.record_size = record_size
        self.fields = {f.name: f for f in fields}
        self.num_records = 0

    async def load(self) -> List[Dict[str, Any]]:
        """Load all records from struct file."""
        records = []
        with open(self.filename, 'rb') as f:
            # First record stores count
            count_data = f.read(self.record_size)
            self.num_records = struct.unpack('<H', count_data[:2])[0]

            # Read each record
            for i in range(self.num_records):
                record_data = f.read(self.record_size)
                record = self.parse_record(record_data)
                records.append(record)

        return records

    def parse_record(self, data: bytes) -> Dict[str, Any]:
        """Parse a single record."""
        record = {}
        for name, field in self.fields.items():
            field_data = data[field.offset:field.offset + field.length]

            if field.type == 'string':
                # Null-terminated string
                value = field_data.split(b'\x00')[0].decode('petscii', errors='replace')
            elif field.type == 'int':
                value = struct.unpack('<H', field_data[:2])[0]
            elif field.type == 'date':
                # BCD encoded date: YYMMDDHHmm
                value = self.parse_bcd_date(field_data)
            elif field.type == 'flags':
                value = field_data

            record[name] = value

        return record

    async def save(self, records: List[Dict[str, Any]]):
        """Save records to struct file."""
        with open(self.filename, 'wb') as f:
            # Write count in first record
            count_data = struct.pack('<H', len(records))
            count_data += b'\x00' * (self.record_size - 2)
            f.write(count_data)

            # Write each record
            for record in records:
                record_data = self.build_record(record)
                f.write(record_data)

    def build_record(self, record: Dict[str, Any]) -> bytes:
        """Build binary record from dict."""
        data = bytearray(self.record_size)

        for name, value in record.items():
            field = self.fields[name]

            if field.type == 'string':
                encoded = value.encode('petscii')[:field.length-1]
                data[field.offset:field.offset+len(encoded)] = encoded
            elif field.type == 'int':
                struct.pack_into('<H', data, field.offset, value)
            elif field.type == 'date':
                date_bcd = self.encode_bcd_date(value)
                data[field.offset:field.offset+len(date_bcd)] = date_bcd
            elif field.type == 'flags':
                data[field.offset:field.offset+len(value)] = value

        return bytes(data)

    @staticmethod
    def parse_bcd_date(data: bytes) -> str:
        """Parse BCD-encoded date: YYMMDDHHmm."""
        # BCD: each nibble is a decimal digit
        digits = []
        for byte in data[:5]:
            digits.append((byte >> 4) & 0x0f)
            digits.append(byte & 0x0f)
        return ''.join(str(d) for d in digits)

    @staticmethod
    def encode_bcd_date(date_str: str) -> bytes:
        """Encode date string to BCD format."""
        # Convert "2501041530" to BCD bytes
        digits = [int(d) for d in date_str[:10]]
        bcd_bytes = []
        for i in range(0, 10, 2):
            byte = (digits[i] << 4) | digits[i+1]
            bcd_bytes.append(byte)
        return bytes(bcd_bytes)

# Example struct definitions
MESSAGE_STRUCT = StructFile(
    "messages.dat",
    record_size=256,
    fields=[
        StructField("author", 0, 20, "string"),
        StructField("subject", 20, 40, "string"),
        StructField("date", 60, 5, "date"),
        StructField("access", 65, 1, "int"),
        StructField("flags", 66, 2, "flags"),
        StructField("body_offset", 68, 4, "int"),
    ]
)
```

### Relative File Emulation (data/relative.py)

```python
"""
Relative (random access) file emulation.

C64 relative files allow direct record access by record number.
We emulate this with Python file seeking.
"""

class RelativeFile:
    """Emulate C64 relative file access."""

    def __init__(self, filename: str, record_size: int):
        self.filename = filename
        self.record_size = record_size
        self.file = None

    async def open(self, mode: str = 'r+b'):
        """Open the relative file."""
        self.file = open(self.filename, mode)

    async def close(self):
        """Close the relative file."""
        if self.file:
            self.file.close()
            self.file = None

    async def read_record(self, record_num: int) -> bytes:
        """Read a specific record by number (1-indexed)."""
        offset = (record_num - 1) * self.record_size
        self.file.seek(offset)
        return self.file.read(self.record_size)

    async def write_record(self, record_num: int, data: bytes):
        """Write a specific record by number (1-indexed)."""
        if len(data) != self.record_size:
            raise ValueError(f"Data must be exactly {self.record_size} bytes")
        offset = (record_num - 1) * self.record_size
        self.file.seek(offset)
        self.file.write(data)

    async def get_record_count(self) -> int:
        """Get total number of records."""
        self.file.seek(0, 2)  # Seek to end
        size = self.file.tell()
        return size // self.record_size
```

---

## Command System

### Command Base Class (commands/base.py)

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class CommandInfo:
    """Command metadata."""
    name: str
    aliases: List[str]
    description: str
    access_level: int = 0
    local_only: bool = False
    cost: int = 0  # Credit cost

class Command(ABC):
    """Base class for BBS commands."""

    info: CommandInfo

    @abstractmethod
    async def execute(self, session: 'Session', args: str = ""):
        """Execute the command."""
        pass

    async def check_access(self, session: 'Session') -> bool:
        """Check if user has access to this command."""
        if session.context.access_level < self.info.access_level:
            return False
        if self.info.local_only and not session.flags.check(Flag.LOCAL_MODE):
            return False
        return True

    async def charge_credits(self, session: 'Session'):
        """Charge user credits for command."""
        if self.info.cost > 0:
            session.context.user.credits -= self.info.cost
            await session.bbs.storage.users.save(session.context.user)

# Example command implementation
class TimeCommand(Command):
    """Display current time and date."""

    info = CommandInfo(
        name="T",
        aliases=["TIME"],
        description="Display time and date",
        access_level=0
    )

    async def execute(self, session: 'Session', args: str = ""):
        """Show current time."""
        now = datetime.now()
        time_str = now.strftime("%a %b %d, %Y %I:%M %p")
        await session.terminal.output(f"{time_str}\n")

        # Show time remaining
        mins = session.context.time_remaining
        if mins == 9999:
            time_left = "--:--"
        else:
            hours = mins // 60
            mins = mins % 60
            time_left = f"{hours:02d}:{mins:02d}"
        await session.terminal.output(f"Time remaining: {time_left}\n")
```

### Command Registry (commands/registry.py)

```python
from typing import Dict, Optional
from .base import Command

class CommandRegistry:
    """Registry of all available commands."""

    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.aliases: Dict[str, str] = {}

    def register(self, command: Command):
        """Register a command."""
        self.commands[command.info.name] = command
        for alias in command.info.aliases:
            self.aliases[alias] = command.info.name

    def parse(self, command_str: str) -> Optional[Command]:
        """Parse command string and return Command instance."""
        # Split command and args
        parts = command_str.strip().split(None, 1)
        if not parts:
            return None

        cmd_name = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""

        # Resolve alias
        if cmd_name in self.aliases:
            cmd_name = self.aliases[cmd_name]

        # Get command
        command = self.commands.get(cmd_name)
        if command:
            # Store args for execute()
            command._args = args

        return command

    def get_help_text(self, access_level: int = 0) -> str:
        """Get help text for available commands."""
        lines = ["Available commands:", ""]
        for cmd in sorted(self.commands.values(), key=lambda c: c.info.name):
            if cmd.info.access_level <= access_level:
                lines.append(f"  {cmd.info.name:6s} - {cmd.info.description}")
        return '\n'.join(lines)
```

### Command Parser with Ranges (commands/parser.py)

```python
"""
Command parser supporting range specifications.

Examples:
  L      - List all
  L5     - List item 5
  L5-10  - List items 5 through 10
  L5-    - List items 5 to end
"""

from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class CommandRange:
    """Parsed command range."""
    start: Optional[int] = None
    end: Optional[int] = None

    def __bool__(self):
        return self.start is not None

    def items(self, max_items: int) -> range:
        """Get range of items."""
        start = self.start or 1
        end = self.end or max_items
        return range(start, end + 1)

def parse_range(args: str) -> Tuple[str, CommandRange]:
    """
    Parse command with optional range.

    Returns (command, range) tuple.
    """
    args = args.strip()
    if not args:
        return "", CommandRange()

    # Check for range at end
    parts = args.split()
    if not parts:
        return "", CommandRange()

    cmd = parts[0]
    range_spec = parts[1] if len(parts) > 1 else ""

    # Try to parse range from command itself
    # e.g., "L5-10" -> cmd="L", range="5-10"
    if cmd[0].isalpha() and len(cmd) > 1:
        range_spec = cmd[1:]
        cmd = cmd[0]

    # Parse range spec
    cmd_range = CommandRange()
    if range_spec:
        if '-' in range_spec:
            # Range: "5-10" or "5-"
            start, end = range_spec.split('-', 1)
            cmd_range.start = int(start) if start else None
            cmd_range.end = int(end) if end else None
        else:
            # Single item: "5"
            cmd_range.start = int(range_spec)
            cmd_range.end = int(range_spec)

    return cmd, cmd_range
```

---

## Session Management

### User Flags (system/flags.py)

```python
from enum import IntEnum

class Flag(IntEnum):
    """User and system flags (matching v2 lightbar positions)."""
    # Page 1 (System)
    SYSOP_AVAILABLE = 0
    BACKGROUND_PAGE = 1
    EDIT_ACCESS = 2
    BLOCK_300_BAUD = 3
    LOCAL_MODE = 4
    PSEUDO_LOCAL = 5
    EDIT_TIME = 6
    PRIME_TIME = 7
    CHAT_MODE = 8
    DISABLE_MODEM = 9
    NEW_USERS_DISALLOWED = 10
    SCREEN_BLANKING = 11
    PRINT_SPOOLING = 12
    PRINT_LOG = 13
    UD_DISABLED = 14
    UD_300_LOCKOUT = 15

    # Page 2 (Terminal)
    ASCII_TRANSLATION = 16
    LINEFEEDS = 17
    ANSI_COLOR = 18
    ANSI_GRAPHICS = 19
    EXPERT_MODE = 20
    NO_DOUBLE_CALLS = 21
    NO_IMMEDIATE_CREDITS = 22
    AUTO_LOGOFF = 23
    TRACE_ENABLE = 24
    UNDEFINED_25 = 25
    LOCAL_BELLS = 26
    LOCAL_BEEPS_DISABLE = 27
    NETMAIL_ENABLE = 28
    NETMAIL_TRIGGER = 29
    MACROS_ENABLE = 30
    MCI_DISABLE = 31

    # Page 3 (Features)
    MAILCHECK_AT_LOGON = 32
    EXCESSIVE_CHAT_LOGOFF = 33
    MORE_PROMPT = 34
    MORE_UNAVAILABLE = 35
    FULLCOLOR_READ_DISABLE = 36
    UNDEFINED_37 = 37
    SUBBOARDS_CLOSED = 38
    FILES_CLOSED = 39
    SYSTEM_RESERVED = 40
    NETWORK_RESERVE = 41
    UNDEFINED_42 = 42
    MODEM_ANSWER_DISABLED = 43
    IN_MENU_MODE = 44
    MENUS_AVAILABLE = 45
    UNDEFINED_46 = 46
    EXPRESS_LOGIN = 47

    # Pages 4-6 undefined (48-95)

    # Page 7 (Alarms)
    ALARM_1_ENABLE = 96
    ALARM_1_TRIGGER = 97
    ALARM_2_ENABLE = 98
    ALARM_2_TRIGGER = 99
    ALARM_3_ENABLE = 100
    ALARM_3_TRIGGER = 101
    ALARM_4_ENABLE = 102
    ALARM_4_TRIGGER = 103
    ALARM_5_ENABLE = 104
    ALARM_5_TRIGGER = 105
    ALARM_6_ENABLE = 106
    ALARM_6_TRIGGER = 107
    ALARM_7_ENABLE = 108
    ALARM_7_TRIGGER = 109
    ALARM_8_ENABLE = 110
    ALARM_8_TRIGGER = 111

class UserFlags:
    """User flag management (20 flags from file-formats.txt)."""

    def __init__(self, flag_string: str = "19111911111111190000"):
        """Initialize from flag string."""
        self.flags = list(flag_string)

    def get(self, index: int) -> str:
        """Get flag at index (0-19)."""
        if 0 <= index < len(self.flags):
            return self.flags[index]
        return '0'

    def set(self, index: int, value: str):
        """Set flag at index."""
        if 0 <= index < len(self.flags):
            self.flags[index] = value

    def to_string(self) -> str:
        """Convert to string format."""
        return ''.join(self.flags)

    # Flag accessors based on command-appendix.md
    @property
    def non_weed(self) -> bool:
        """Non-weed status (flag 0)."""
        return self.flags[0] != '0'

    @property
    def credit_ratio(self) -> int:
        """Credit ratio 1-9 (flag 1)."""
        return int(self.flags[1])

    @property
    def local_maint(self) -> bool:
        """Local maintenance access (flag 2)."""
        return self.flags[2] != '0'

    @property
    def can_post(self) -> bool:
        """Post/respond capability (flag 3)."""
        return self.flags[3] != '0'

    @property
    def can_ud(self) -> bool:
        """UD/UX access (flag 4)."""
        return self.flags[4] != '0'

    @property
    def max_editor_lines(self) -> int:
        """Maximum editor lines (flag 5): 0=10, 1=20, ... 9=100."""
        return (int(self.flags[5]) + 1) * 10

    # ... more flag accessors

class LightbarFlags:
    """System lightbar flags (128 flags across 8 pages)."""

    def __init__(self):
        self.flags = [False] * 128

    def check(self, flag: Flag) -> bool:
        """Check if flag is set."""
        return self.flags[flag]

    def set(self, flag: Flag, value: bool = True):
        """Set flag value."""
        self.flags[flag] = value

    def toggle(self, flag: Flag):
        """Toggle flag."""
        self.flags[flag] = not self.flags[flag]

    def clear(self, flag: Flag):
        """Clear flag."""
        self.flags[flag] = False

    async def load_defaults(self, storage):
        """Load default lightbar settings from e.lightdefs."""
        # Read e.lightdefs file (8 lines, 16 chars each)
        pass

    async def save_defaults(self, storage):
        """Save current lightbar settings to e.lightdefs."""
        pass
```

### Access Control (system/access.py)

```python
"""Access level and permission checking."""

class AccessLevel(IntEnum):
    """Access levels 0-9."""
    NEW_USER = 0
    GUEST = 1
    USER = 2
    REGULAR = 3
    VALIDATED = 4
    SUBOP = 5
    ASSISTANT_SYSOP = 6
    CO_SYSOP = 7
    SYSOP = 8
    ADMIN = 9

def check_access(user_level: int, required_level: int) -> bool:
    """Check if user has required access level."""
    return user_level >= required_level

def check_flag(user: User, flag_index: int) -> bool:
    """Check if user has specific flag set."""
    flags = UserFlags(user.flags)
    return flags.get(flag_index) != '0'

def check_permission(user: User, permission: str) -> bool:
    """Check complex permission (access + flags)."""
    if permission == "post":
        flags = UserFlags(user.flags)
        return flags.can_post and user.access_level >= AccessLevel.USER
    elif permission == "upload":
        flags = UserFlags(user.flags)
        return flags.can_ud and user.access_level >= AccessLevel.VALIDATED
    elif permission == "local_maint":
        flags = UserFlags(user.flags)
        return flags.local_maint and user.access_level >= AccessLevel.SUBOP
    # ... more permissions
    return False
```

---

## Extension System

### Module Loader (extensions/loader.py)

```python
"""
Plus-file module loader.

Emulates v2's dynamic module loading system where modules are loaded
on demand with 'load "+.name"' or 'load "i.name"'.
"""

from typing import Optional, Dict, Any
import importlib

class ModuleLoader:
    """Dynamic module loader for plus-files."""

    def __init__(self, bbs: 'ImageBBS'):
        self.bbs = bbs
        self.loaded_modules: Dict[str, Any] = {}

    async def load_plus_module(self, name: str, session: 'Session'):
        """
        Load a plus-file module.

        Module types:
        - +.name  -> extensions/modules/name.py
        - i.name  -> extensions/modules/i_name.py (goto 3000)
        - i/name  -> extensions/modules/i_name.py (goto 4000)
        - sub.name -> extensions/modules/sub_name.py (gosub 60000)
        """
        # Translate module name
        module_name = name.replace('+.', '').replace('i.', 'i_').replace('/', '_')

        # Check if already loaded
        if module_name in self.loaded_modules:
            module = self.loaded_modules[module_name]
        else:
            # Import module
            try:
                module_path = f'imagebbs.extensions.modules.{module_name}'
                module = importlib.import_module(module_path)
                self.loaded_modules[module_name] = module
            except ImportError:
                await session.terminal.output(f"Module not found: {name}\n")
                return

        # Execute module entry point
        if hasattr(module, 'execute'):
            await module.execute(session)
        else:
            await session.terminal.output(f"Module {name} has no entry point\n")

    async def reload_module(self, name: str):
        """Reload a module (for development)."""
        if name in self.loaded_modules:
            module = self.loaded_modules[name]
            importlib.reload(module)
```

### ECS (Extended Command Set) (extensions/ecs.py)

```python
"""
Extended Command Set - custom command definitions.

Allows sysops to define custom commands with access levels,
passwords, and credit costs.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ECSCommand:
    """ECS command definition."""
    name: str
    password: Optional[str]
    access_level: int
    credits: int
    goto_line: int  # For GOTO commands
    flags: int

class ECSSystem:
    """ECS command manager."""

    def __init__(self, storage):
        self.storage = storage
        self.commands: Dict[str, ECSCommand] = {}

    async def load(self):
        """Load ECS definitions from e.ecs.main."""
        # Read struct file
        pass

    async def save(self):
        """Save ECS definitions to e.ecs.main."""
        pass

    async def check_command(self, command: str, session: 'Session') -> Optional[ECSCommand]:
        """Check if command is an ECS command and user has access."""
        cmd = self.commands.get(command.upper())
        if not cmd:
            return None

        # Check access level
        if session.context.access_level < cmd.access_level:
            return None

        # Check password if required
        if cmd.password:
            password = await session.terminal.input_password("Password: ")
            if password != cmd.password:
                return None

        # Check credits
        if cmd.credits > session.context.user.credits:
            await session.terminal.output("Insufficient credits.\n")
            return None

        return cmd

    async def execute(self, cmd: ECSCommand, session: 'Session'):
        """Execute ECS command."""
        # Charge credits
        if cmd.credits:
            session.context.user.credits -= cmd.credits
            await session.bbs.storage.users.save(session.context.user)

        # Execute GOTO
        if cmd.goto_line:
            # Load module at goto_line
            module_name = f"ecs_{cmd.goto_line}"
            await session.bbs.loader.load_plus_module(module_name, session)
```

---

## Configuration

### Settings (config/settings.py)

```python
"""Application settings."""

from pathlib import Path
from pydantic import BaseSettings, Field

class BBSConfig(BaseSettings):
    """BBS configuration."""

    # Server settings
    bbs_name: str = "Image BBS"
    sysop_name: str = "Sysop"
    telnet_host: str = "0.0.0.0"
    telnet_port: int = 6400

    # Paths
    data_path: Path = Field(default_factory=lambda: Path("data"))
    text_files_path: Path = Field(default_factory=lambda: Path("data/text"))
    plus_files_path: Path = Field(default_factory=lambda: Path("data/plus"))

    # Time limits (minutes by access level)
    time_limits: dict[int, int] = {
        0: 30,   # New user
        1: 45,   # Guest
        2: 60,   # User
        3: 90,   # Regular
        4: 120,  # Validated
        5: 180,  # SubOp
        6: 240,  # Assistant Sysop
        7: 360,  # Co-Sysop
        8: 9999, # Sysop
        9: 9999, # Admin
    }

    # Prime time
    prime_time_enabled: bool = False
    prime_time_start: str = "18:00"
    prime_time_end: str = "23:00"
    prime_time_limit: int = 30

    # Feature flags
    allow_new_users: bool = True
    allow_guest_login: bool = True
    require_email_validation: bool = False

    # Logging
    log_level: str = "INFO"
    log_file: Path = Field(default_factory=lambda: Path("logs/imagebbs.log"))
    activity_log: Path = Field(default_factory=lambda: Path("data/logs/activity.log"))

    class Config:
        env_prefix = "IMAGEBBS_"
        env_file = ".env"
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_terminal.py
import pytest
from imagebbs.terminal.petscii import petscii_to_unicode, unicode_to_petscii

def test_petscii_roundtrip():
    """Test PETSCII encoding/decoding roundtrip."""
    original = "HELLO WORLD"
    petscii = unicode_to_petscii(original)
    decoded = petscii_to_unicode(petscii)
    assert decoded == original

# tests/test_commands.py
import pytest
from imagebbs.commands.parser import parse_range

def test_parse_range():
    """Test command range parsing."""
    cmd, rng = parse_range("L5-10")
    assert cmd == "L"
    assert rng.start == 5
    assert rng.end == 10

def test_parse_single():
    """Test single item parsing."""
    cmd, rng = parse_range("L5")
    assert cmd == "L"
    assert rng.start == 5
    assert rng.end == 5

def test_parse_open_range():
    """Test open-ended range."""
    cmd, rng = parse_range("L5-")
    assert cmd == "L"
    assert rng.start == 5
    assert rng.end is None
```

### Integration Tests

```python
# tests/integration/test_session.py
import pytest
from imagebbs.core.bbs import ImageBBS
from imagebbs.core.session import Session

@pytest.mark.asyncio
async def test_login_flow():
    """Test complete login flow."""
    bbs = ImageBBS(test_config)
    await bbs.start()

    # Simulate connection
    reader, writer = await create_test_connection()
    session = Session(bbs, reader, writer)

    # Send login credentials
    writer.write(b"TESTUSER\r\n")
    writer.write(b"password\r\n")

    # Check session state
    assert session.context.user is not None
    assert session.context.user.handle == "TESTUSER"
```

### Load Testing

```python
# tests/load/test_concurrent_users.py
import asyncio
import pytest

@pytest.mark.asyncio
async def test_100_concurrent_users():
    """Test BBS with 100 concurrent connections."""
    bbs = ImageBBS(test_config)
    await bbs.start()

    # Create 100 concurrent sessions
    sessions = []
    for i in range(100):
        session = await create_test_session(bbs, f"USER{i}")
        sessions.append(session)

    # Run for 1 minute
    await asyncio.sleep(60)

    # Verify all sessions active
    assert len(bbs.sessions) == 100
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up project structure
- [ ] Implement terminal I/O base classes
- [ ] Implement PETSCII/ASCII/ANSI encoding
- [ ] Implement telnet protocol handler
- [ ] Basic session management

### Phase 2: Data Layer (Weeks 3-4)
- [ ] Sequential file I/O
- [ ] Relative file emulation
- [ ] Struct file format
- [ ] User storage
- [ ] Basic configuration

### Phase 3: Core Features (Weeks 5-8)
- [ ] Login/authentication system
- [ ] Main command loop
- [ ] Command registry and parser
- [ ] Basic commands (T, ST, Q, O)
- [ ] Lightbar system basics
- [ ] User flags and access control

### Phase 4: Messaging (Weeks 9-12)
- [ ] Message base system
- [ ] Post/read/list messages
- [ ] Email system
- [ ] Feedback system

### Phase 5: Files (Weeks 13-16)
- [ ] File library system
- [ ] XMODEM protocol
- [ ] Upload/download operations
- [ ] Credit system

### Phase 6: Advanced Features (Weeks 17-20)
- [ ] Text editor
- [ ] MCI parser
- [ ] ECS system
- [ ] Plus-file loader
- [ ] Local maintenance commands

### Phase 7: Polish & Testing (Weeks 21-24)
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation
- [ ] Migration tools (import v2 data)

---

## Migration Strategy

### Importing v2 Data

```python
# tools/import_v2.py
"""Import data from ImageBBS v2."""

class V2Importer:
    """Import v2 BBS data to Python port."""

    async def import_users(self, v2_path: Path):
        """Import u.config and u.index."""
        # Read v2 u.config format
        # Convert to Python format
        pass

    async def import_messages(self, v2_path: Path):
        """Import message bases."""
        # Read v2 message files
        # Convert to Python format
        pass

    async def import_files(self, v2_path: Path):
        """Import file libraries."""
        # Read v2 file listings
        # Copy actual files
        pass
```

---

## Next Steps

1. **Create project structure**: Set up `src/imagebbs/` directory tree
2. **Implement core classes**: Start with BBS, Session, Terminal base classes
3. **Build terminal layer**: PETSCII encoding, ANSI translation
4. **Add telnet server**: Get basic connections working
5. **Implement login**: User authentication and session setup

This architecture provides a solid foundation for recreating ImageBBS in Python while maintaining the authentic experience and supporting modern platforms.
