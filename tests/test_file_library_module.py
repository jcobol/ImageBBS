from pathlib import Path

from imagebbs.runtime.file_library import (
    FileLibraryEvent,
    FileLibraryModule,
)
from imagebbs.runtime.file_transfers import (
    FileTransferEvent,
    FileTransfersModule,
)
from imagebbs.session_kernel import SessionKernel, SessionState
from imagebbs.setup_defaults import SetupDefaults
from imagebbs.storage_config import DriveMapping, StorageConfig


def _bootstrap_kernel() -> tuple[SessionKernel, FileTransfersModule]:
    module = FileTransfersModule()
    kernel = SessionKernel(module=module)
    return kernel, module


def _bootstrap_kernel_with_storage(
    root: Path, *, read_only: bool = False
) -> tuple[SessionKernel, FileTransfersModule, Path]:
    drive_root = root / "drive8"
    library_root = drive_root / "ud" / "main"
    library_root.mkdir(parents=True, exist_ok=True)
    (library_root / "HOSTFILE.SEQ").write_bytes(b"x" * 600)
    defaults = SetupDefaults.stub()
    storage = StorageConfig(
        drives={8: DriveMapping(drive=8, root=drive_root, read_only=read_only)},
        default_drive=8,
    )
    object.__setattr__(defaults, "storage_config", storage)
    object.__setattr__(defaults, "filesystem_drive_roots", {8: drive_root})
    object.__setattr__(defaults, "filesystem_drive_slots", {8: 1})
    object.__setattr__(defaults, "default_filesystem_drive", 8)
    object.__setattr__(defaults, "default_filesystem_drive_slot", 1)
    module = FileTransfersModule()
    kernel = SessionKernel(module=module, defaults=defaults)
    return kernel, module, library_root


def test_ud_command_enters_library_module() -> None:
    kernel, _ = _bootstrap_kernel()
    console = kernel.services["console"]
    kernel.step(FileTransferEvent.ENTER)
    console.device.output.clear()

    state = kernel.step(FileTransferEvent.COMMAND, "UD")

    assert state is SessionState.FILE_LIBRARY
    assert isinstance(kernel.module, FileLibraryModule)

    kernel.step(FileLibraryEvent.ENTER)
    output = "".join(console.device.output)
    assert "Library: Main U/D" in output
    assert "*** IMAGE U/D ***" in output


def test_library_module_lists_and_moves() -> None:
    kernel, _ = _bootstrap_kernel()
    kernel.step(FileTransferEvent.ENTER)
    kernel.step(FileTransferEvent.COMMAND, "UD")

    module = kernel.module
    assert isinstance(module, FileLibraryModule)

    kernel.step(FileLibraryEvent.ENTER)
    console = kernel.services["console"]
    console.device.output.clear()

    kernel.step(FileLibraryEvent.COMMAND, "L")

    output = "".join(console.device.output)
    assert "1: Main U/D" in output
    assert "2: Main U/D / Games" in output

    console.device.output.clear()
    kernel.step(FileLibraryEvent.COMMAND, "M 2")
    moved_output = "".join(console.device.output)
    assert "Moved to Main U/D / Games." in moved_output
    assert module._active_identifier == "2"


def test_library_module_adds_and_deletes_entries() -> None:
    kernel, _ = _bootstrap_kernel()
    kernel.step(FileTransferEvent.ENTER)
    kernel.step(FileTransferEvent.COMMAND, "UD")
    module = kernel.module
    assert isinstance(module, FileLibraryModule)

    kernel.step(FileLibraryEvent.ENTER)
    console = kernel.services["console"]
    console.device.output.clear()

    kernel.step(FileLibraryEvent.COMMAND, "S")
    assert "No entries" not in "".join(console.device.output)

    console.device.output.clear()
    kernel.step(FileLibraryEvent.COMMAND, "A STARMAP 5 Star chart")
    output = "".join(console.device.output)
    assert "Added STARMAP" in output

    console.device.output.clear()
    kernel.step(FileLibraryEvent.COMMAND, "S")
    listing = "".join(console.device.output)
    assert "STARMAP" in listing

    console.device.output.clear()
    kernel.step(FileLibraryEvent.COMMAND, "K 3")
    removal = "".join(console.device.output)
    assert "Removed entry #3" in removal


def test_library_module_prefers_host_entries(tmp_path: Path) -> None:
    kernel, _module, library_root = _bootstrap_kernel_with_storage(tmp_path)
    kernel.step(FileTransferEvent.ENTER)
    kernel.step(FileTransferEvent.COMMAND, "UD")

    module = kernel.module
    assert isinstance(module, FileLibraryModule)

    kernel.step(FileLibraryEvent.ENTER)
    console = kernel.services["console"]
    console.device.output.clear()

    kernel.step(FileLibraryEvent.COMMAND, "S")

    output = "".join(console.device.output)
    assert "HOSTFILE.SEQ" in output
    assert "SPACE.DOC" not in output
    assert library_root.is_dir()


def test_library_module_adds_to_host_directory(tmp_path: Path) -> None:
    kernel, _module, _ = _bootstrap_kernel_with_storage(tmp_path)
    kernel.step(FileTransferEvent.ENTER)
    kernel.step(FileTransferEvent.COMMAND, "UD")

    module = kernel.module
    assert isinstance(module, FileLibraryModule)

    kernel.step(FileLibraryEvent.ENTER)
    console = kernel.services["console"]
    console.device.output.clear()

    kernel.step(FileLibraryEvent.COMMAND, "A NEWFILE 3 Demo file")
    output = "".join(console.device.output)
    assert "Added NEWFILE" in output

    console.device.output.clear()
    kernel.step(FileLibraryEvent.COMMAND, "S")
    listing = "".join(console.device.output)
    assert "NEWFILE" in listing


def test_library_module_rejects_read_only_host_directory(tmp_path: Path) -> None:
    kernel, _module, _ = _bootstrap_kernel_with_storage(tmp_path, read_only=True)
    kernel.step(FileTransferEvent.ENTER)
    kernel.step(FileTransferEvent.COMMAND, "UD")

    module = kernel.module
    assert isinstance(module, FileLibraryModule)

    kernel.step(FileLibraryEvent.ENTER)
    console = kernel.services["console"]
    console.device.output.clear()

    kernel.step(FileLibraryEvent.COMMAND, "A BLOCKED 1")
    output = "".join(console.device.output)
    assert "?DRIVE IS READ-ONLY" in output

