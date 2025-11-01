"""Tests for the ``mirror_module`` compatibility helper."""
from __future__ import annotations

import sys
from types import ModuleType

from imagebbs._compat import mirror_module


# Why: Validate that ``mirror_module`` mirrors exports and forwards lookups for modules with varied ``__all__`` declarations.
def test_mirror_module_exports_and_forwarders() -> None:
    explicit_name = "tests.fake_compat_module_explicit"
    implicit_name = "tests.fake_compat_module_implicit"

    explicit_module = ModuleType(explicit_name)
    explicit_module.__doc__ = "Explicit module docstring"
    explicit_module.__all__ = ["exported_value", "ExportedClass"]
    explicit_module.exported_value = 42

    class ExportedClass:  # pragma: no cover - type placeholder only
        """Sentinel class for testing export mirroring."""

    explicit_module.ExportedClass = ExportedClass
    explicit_module.extra_attribute = "extra"
    explicit_module._hidden = "hidden"

    implicit_module = ModuleType(implicit_name)
    implicit_module.__doc__ = "Implicit module docstring"
    implicit_module.alpha = "alpha"
    implicit_module.beta = 99
    implicit_module._gamma = "gamma"

    prior_modules = {explicit_name: sys.modules.get(explicit_name), implicit_name: sys.modules.get(implicit_name)}
    try:
        sys.modules[explicit_name] = explicit_module
        sys.modules[implicit_name] = implicit_module

        explicit_globals: dict[str, object] = {}
        implicit_globals: dict[str, object] = {}

        mirrored_explicit = mirror_module(explicit_globals, explicit_name)
        mirrored_implicit = mirror_module(implicit_globals, implicit_name)

        assert mirrored_explicit is explicit_module
        assert mirrored_implicit is implicit_module

        assert explicit_globals["exported_value"] == explicit_module.exported_value
        assert explicit_globals["ExportedClass"] is explicit_module.ExportedClass
        assert explicit_globals["__doc__"] == explicit_module.__doc__
        assert explicit_globals["__all__"] == explicit_module.__all__

        assert implicit_globals["alpha"] == implicit_module.alpha
        assert implicit_globals["beta"] == implicit_module.beta
        assert implicit_globals["__doc__"] == implicit_module.__doc__
        assert implicit_globals["__all__"] == ["alpha", "beta"]

        explicit_getattr = explicit_globals["__getattr__"]
        implicit_getattr = implicit_globals["__getattr__"]
        assert callable(explicit_getattr)
        assert callable(implicit_getattr)
        assert explicit_getattr("extra_attribute") == explicit_module.extra_attribute
        assert implicit_getattr("_gamma") == implicit_module._gamma

        explicit_dir = explicit_globals["__dir__"]()
        implicit_dir = implicit_globals["__dir__"]()
        assert "exported_value" in explicit_dir
        assert "ExportedClass" in explicit_dir
        assert "extra_attribute" in explicit_dir
        assert "alpha" in implicit_dir
        assert "beta" in implicit_dir
        assert "_gamma" in implicit_dir
    finally:
        for name, prior in prior_modules.items():
            if prior is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = prior
