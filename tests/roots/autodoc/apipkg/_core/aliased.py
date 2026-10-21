# SPDX-License-Identifier: MPL-2.0
"""A module only reachable through an alias, i.e. not importable as `apipkg.aliased`."""


class Aliased:
    """A class in an aliased module."""

    attr: int = 1
    """An attribute."""

    def meth(self) -> None:
        """A method."""
