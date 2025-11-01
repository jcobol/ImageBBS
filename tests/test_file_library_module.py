from imagebbs.runtime.file_library import (
    FileLibraryEvent,
    FileLibraryModule,
)
from imagebbs.runtime.file_transfers import (
    FileTransferEvent,
    FileTransfersModule,
)
from imagebbs.session_kernel import SessionKernel, SessionState


def _bootstrap_kernel() -> tuple[SessionKernel, FileTransfersModule]:
    module = FileTransfersModule()
    kernel = SessionKernel(module=module)
    return kernel, module


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


