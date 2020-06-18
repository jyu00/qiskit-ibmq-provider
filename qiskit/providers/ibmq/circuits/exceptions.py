# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 202.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Exceptions related to IBM Quantum Experience jobs."""

from qiskit.providers.exceptions import JobError, JobTimeoutError

from ..exceptions import IBMQError


class IBMQCircuitError(IBMQError):
    """Base class for errors raised by the circuit modules."""
    pass


class IBMQCircuitNotFound(IBMQCircuitError):
    """Raised when a named circuit is not found."""


class IBMQCircuitBadArguments(IBMQCircuitError):
    """Raised when invalid circuit arguments are used."""
