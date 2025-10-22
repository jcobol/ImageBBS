"""Wrapper for the prototype module."""
from __future__ import annotations

from importlib import import_module
from typing import Iterable, Mapping

from ._compat import mirror_module

_TARGET = mirror_module(globals(), "scripts.prototypes.device_context")

# Populate globals for prototype symbols that fall outside ``__all__``.
DriveAssignment = _TARGET.DriveAssignment
FilesystemDriveLocator = _TARGET.FilesystemDriveLocator

# Ensure runtime overrides reuse the prototype device helpers.
DiskDrive = _TARGET.DiskDrive
MaskedPaneBuffers = _TARGET.MaskedPaneBuffers


class ConsoleService(_TARGET.ConsoleService):
    """Console service exposing ImageBBS-specific helpers."""

    @property
    def masked_pane_staging_map(self) -> "MaskedPaneStagingMap":
        """Return the cached staging map built from native helpers."""

        staging_map = self._masked_pane_staging_map
        if staging_map is None:
            from .runtime.masked_pane_staging import build_masked_pane_staging_map

            staging_map = build_masked_pane_staging_map(self)
            self._masked_pane_staging_map = staging_map
        return staging_map


class DeviceContext(_TARGET.DeviceContext):
    """Device context that wires ImageBBS runtime helpers."""

    def register_console_device(self, console: Console | None = None) -> ConsoleService:
        """Register a console device and expose the ImageBBS wrapper."""

        device = console or Console()
        self.register(device.name, device)
        service = ConsoleService(device)
        self.register_service(service.name, service)
        return service


def bootstrap_device_context(
    assignments: Iterable[DriveAssignment],
    *,
    ampersand_overrides: Mapping[int, str] | None = None,
) -> DeviceContext:
    """Instantiate a device context with modern drive mappings."""

    context = DeviceContext()
    console_service = context.register_console_device()
    context.register_modem_device()
    context.register_ampersand_dispatcher(override_imports=ampersand_overrides)
    context.register_service("device_context", context)
    masked_pane_buffers = MaskedPaneBuffers()
    console_service.capture_masked_pane_buffers(masked_pane_buffers)
    console_service.set_masked_pane_buffers(masked_pane_buffers)
    context.register_service("masked_pane_buffers", masked_pane_buffers)
    for assignment in assignments:
        locator = assignment.locator
        if isinstance(locator, FilesystemDriveLocator):
            device_name = context.drive_device_name(assignment.slot)
            context.register(device_name, DiskDrive(locator.path))
            context.open(device_name, assignment.slot, 15)
    return context


# Ensure prototype helpers see the ImageBBS overrides.
_TARGET.ConsoleService = ConsoleService
_TARGET.DeviceContext = DeviceContext
_TARGET.bootstrap_device_context = bootstrap_device_context

_AMPERSAND_REGISTRY = import_module("scripts.prototypes.ampersand_registry")
_AMPERSAND_REGISTRY.ConsoleService = ConsoleService
