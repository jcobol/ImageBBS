# Repository Instructions for AI Agents

## Project Overview

This repository contains **ImageBBS**, a Commodore 64 bulletin board system (BBS), in multiple versions:

- **v1.2/**: Original Image BBS 1.2 (C64 BASIC + Assembly)
- **v2/**: Image BBS 1.3/2.0 (C64 BASIC + Assembly) - **LEGACY CODE, DO NOT MODIFY**
- **v3/**: Minimal (separate repository exists for full v3)

### Python Port Project (Active Development)

**Goal**: Create a Python port of ImageBBS v2 that recreates the authentic C64 BBS experience while running on modern platforms (Linux, Windows, macOS).

**Target Location**: `src/imagebbs/` (to be created)

The Python port will:
- Look and feel exactly like the original ImageBBS v2
- Support PETSCII, ASCII, and ANSI terminal modes
- Run anywhere Python runs
- Support telnet connections
- Implement all major v2 features (messages, email, file transfers, etc.)

## Important Files

### Documentation

- **ARCHITECTURE.md** - Complete technical architecture for Python port
  - Project structure (12 major modules)
  - Layer design (Protocol → Terminal → Session → Command → Data)
  - Detailed class specifications with code examples
  - 24-week implementation roadmap
  - Testing strategy
  - **READ THIS FIRST** for implementation work

### Legacy Code (Reference Only)

- **v2/** - C64 BASIC and Assembly source (284 BASIC modules, 42 Assembly modules)
  - `v2/core/` - Core BASIC modules (im*.lbl files)
  - `v2/asm/` - Assembly language support
  - `v2/docs/` - Important reference documentation
    - `v2/docs/im-calls.txt` - Function call reference
    - `v2/docs/file-formats.txt` - Data file formats
    - `v2/docs/& commands.txt` - Assembly routine reference (70+ commands)
    - `v2/docs/lightbar.txt` - Lightbar flag system (128 flags)
- **v1.2/docs/command-appendix.md** - Complete user command reference

**⚠️ DO NOT MODIFY v2/ - It is legacy C64 code for reference only**

## Architecture Summary

### Layer Design

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

### Key Technical Challenges

1. **PETSCII Encoding**: C64 character set with graphics characters → Unicode/ANSI
2. **Struct Files**: Custom binary record format used throughout v2
3. **REL Files**: Relative (random access) file emulation
4. **Assembly Calls**: 70+ assembly routines (&,0 through &,71) need Python equivalents
5. **Lightbar System**: 128 flags across 8 pages with complex interactions
6. **Plus-File System**: Dynamic module loading architecture

### Module Structure (Planned)

```
src/imagebbs/
├── core/           # Main BBS engine (bbs.py, session.py)
├── terminal/       # I/O & encoding (petscii.py, ansi.py)
├── protocol/       # Network handlers (telnet.py, xmodem.py)
├── data/           # Storage layer (struct.py, relative.py)
├── models/         # Data models (user.py, message.py)
├── commands/       # Command implementations (general.py, messaging.py)
├── subsystems/     # Major features (messages.py, email.py, files.py)
├── system/         # System mgmt (lightbar.py, flags.py, statistics.py)
├── editor/         # Text editor (line_editor.py, mci.py)
├── extensions/     # Plus-file system (loader.py, ecs.py)
├── network/        # Network features (netmail.py, nodes.py)
├── config/         # Configuration (settings.py)
└── utils/          # Utilities (time.py, formatting.py)
```

## Current Status (as of 2025-11-04)

### Completed
- ✅ Analyzed v2 codebase (284 BASIC + 42 ASM modules)
- ✅ Documented all major features and subsystems
- ✅ Created comprehensive architecture document (ARCHITECTURE.md)
- ✅ Defined complete project structure
- ✅ Established layer design and interfaces
- ✅ Created 24-week implementation roadmap

### Not Yet Started
- ⏸️ `src/imagebbs/` directory creation
- ⏸️ Any Python implementation
- ⏸️ Terminal layer implementation
- ⏸️ Data layer implementation
- ⏸️ Command system implementation

## Next Steps for Implementation

### Immediate (Phase 1: Foundation - Weeks 1-2)

1. **Create project structure**
   ```bash
   mkdir -p src/imagebbs/{core,terminal,protocol,data,models,commands,subsystems,system,editor,extensions,network,config,utils}
   ```

2. **Implement Terminal Layer** (Most visible component)
   - `terminal/base.py` - Base Terminal class
   - `terminal/petscii.py` - PETSCII encoding/decoding
   - `terminal/ansi.py` - ANSI color translation
   - `terminal/ascii_mode.py` - ASCII mode
   - See ARCHITECTURE.md Section: "Terminal Layer"

3. **Implement Telnet Server**
   - `protocol/telnet.py` - Async telnet server
   - Basic connection handling
   - See ARCHITECTURE.md Section: "Protocol & I/O Layer"

4. **Create Core Classes**
   - `core/bbs.py` - Main BBS server
   - `core/session.py` - User session handler
   - `core/context.py` - Session state
   - See ARCHITECTURE.md Section: "Core Architecture"

5. **Basic Configuration**
   - `config/settings.py` - Pydantic settings
   - `.env` file for configuration

### Technology Stack

- **Python 3.10+** (required for modern type hints)
- **asyncio** - Async I/O for telnet
- **telnetlib3** or **asynctelnet** - Telnet protocol
- **structlog** - Structured logging
- **pydantic** - Data validation and settings
- **pytest** - Testing framework

### Priority Order (from ARCHITECTURE.md)

**Critical Path (MVP)**
1. Terminal I/O (telnet, PETSCII/ASCII/ANSI) ← START HERE
2. User management (login, accounts, access)
3. File I/O (sequential, REL, struct)
4. Message bases (post, read, list)
5. Main command loop
6. Basic lightbar system

**High Priority**
7. Email system
8. Upload/Download section
9. File protocols (XMODEM)
10. Editor system
11. Logging & statistics
12. Local maintenance commands

## Key Concepts from v2

### Assembly Command Mapping (&,n)

v2 uses assembly language routines called with `&,command,params`. These need Python equivalents:

| C64 Call | Python Equivalent | Purpose |
|----------|-------------------|---------|
| `&,1` | `session.output.inline()` | Inline text output |
| `&,6` | `session.terminal.input_password()` | Password input |
| `&,52,x,y` | `session.flags.check(Flag.x)` | Check/set lightbar flags |
| `&,60,...` | `storage.struct.*()` | Struct file operations |

See `v2/docs/& commands.txt` for complete reference.

### File Formats

**User Config (u.config)**: 23 fields per user
- Handle, password, name, phone
- Access level (0-9)
- 20 user flags (permissions)
- Statistics (calls, posts, uploads/downloads)
- Last call date/time
- Terminal parameters

**Struct Files**: Binary records with fixed-size fields
- Used for messages, email, file listings, feedback
- First record stores count
- BCD-encoded dates
- See ARCHITECTURE.md "Struct File Format" for implementation

**Relative Files**: Random access by record number
- Python emulation via file.seek()
- 1-indexed record numbers

### Lightbar Flags (128 total)

8 pages × 16 flags = 128 system flags controlling BBS behavior:
- Page 1: System controls (sysop available, local mode, prime time, etc.)
- Page 2: Terminal settings (ASCII/ANSI, expert mode, linefeeds, etc.)
- Page 3: Feature toggles (more prompt, macros, netmail, etc.)
- Pages 4-6: Undefined (extensible)
- Page 7: Alarms (8 alarms × 2 flags each)

See `v2/docs/lightbar.txt` for details.

### User Flags (20 total)

Stored in user record as 20-character string (e.g., "19111911111111190000"):
- Flag 0: Non-weed status (Y/N)
- Flag 1: Credit ratio (1-9)
- Flag 2: Local maintenance access (Y/N)
- Flag 3: Post/respond capability (Y/N)
- Flag 4: UD/UX access (Y/N)
- Flag 5: Max editor lines (0=10, 1=20, ..., 9=100)
- Flags 6-19: Various permissions

See `v1.2/docs/command-appendix.md` "User Flags" section.

## Development Guidelines

### What to Build
- ✅ New Python code in `src/imagebbs/`
- ✅ Tests in `tests/`
- ✅ Documentation in root `.md` files
- ✅ Configuration files (`.env`, `pyproject.toml`, etc.)

### What NOT to Modify
- ❌ **v2/** directory (legacy C64 code)
- ❌ v1.2/ directory (reference only)
- ❌ v3/ directory (separate project)

### Code Style
- Use **async/await** throughout (telnet is async I/O)
- Use **type hints** on all functions
- Use **dataclasses** for simple data structures
- Use **pydantic** for configuration and validation
- Follow **PEP 8** style guide
- Document classes and complex functions

### Testing Strategy
- Write **unit tests** for all core functionality
- Write **integration tests** for command flows
- Test **PETSCII encoding** roundtrips
- Test **file format** compatibility with v2 data
- Load test with multiple concurrent users

## Common Patterns

### Session Access Pattern
```python
async def some_command(session: Session):
    # Access user
    user = session.context.user

    # Check permissions
    if not session.flags.check(Flag.LOCAL_MODE):
        return

    # Output to terminal
    await session.terminal.output("Hello!\n")

    # Get input
    response = await session.terminal.input_line("Continue? ")

    # Access storage
    data = await session.bbs.storage.users.find("HANDLE")
```

### Struct File Pattern
```python
# Load struct
records = await storage.struct.load("messages.dat", MESSAGE_STRUCT)

# Access fields
for record in records:
    author = record["author"]
    date = record["date"]

# Save struct
await storage.struct.save("messages.dat", records)
```

### Command Implementation Pattern
```python
class MyCommand(Command):
    info = CommandInfo(
        name="MC",
        aliases=["MYCMD"],
        description="My command",
        access_level=2
    )

    async def execute(self, session: Session, args: str = ""):
        if not await self.check_access(session):
            await session.terminal.output("Access denied.\n")
            return

        # Command logic here
        await session.terminal.output("Command executed!\n")
```

## Bootstrap Checklist for Next Session

When starting a new session to continue this work:

1. ✅ Read **ARCHITECTURE.md** for complete technical details
2. ✅ Review this file (AGENTS.md) for project context
3. ✅ Check **Current Status** section above
4. ✅ Look at **v2/docs/** for reference on features being ported
5. ✅ Follow **Next Steps** section for what to implement
6. ✅ Use **Common Patterns** for consistent code style
7. ✅ Start with **Terminal Layer** (most visible, foundational)

## Reference Commands

```bash
# Explore v2 codebase structure
find v2/core -name "*.lbl" | wc -l  # 284 BASIC modules
find v2/asm -name "*.asm" | wc -l    # 42 Assembly modules

# View important docs
cat v2/docs/im-calls.txt              # Function reference
cat v2/docs/file-formats.txt          # Data formats
cat v2/docs/lightbar.txt              # Flag system
cat v1.2/docs/command-appendix.md     # User commands

# View architecture
cat ARCHITECTURE.md                    # Full technical design
```

## Questions to Ask User

If continuing this project and unclear about direction:

1. "Should I start implementing Phase 1 (Terminal layer + Telnet)?"
2. "Should I create the complete `src/imagebbs/` directory structure?"
3. "Should I build a specific component like PETSCII encoder or Session class?"
4. "Do you have existing Python code in `src/imagebbs/` I should review first?"

## Important Context Notes

- **This is NOT a web BBS** - It's a telnet BBS that looks like a C64
- **Authenticity matters** - Must look/feel like the original
- **No Python code exists yet** - Starting from scratch
- **v2 is reference only** - Don't modify, only read for understanding
- **24-week roadmap exists** - See ARCHITECTURE.md for phased approach
- **All I/O is async** - Uses asyncio for concurrent user support

