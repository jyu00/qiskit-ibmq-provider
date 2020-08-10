# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Client for accessing circuit services."""

import logging
from typing import List, Dict, Any

from .base import BaseClient
from ..rest import Api
from ..session import RetrySession

logger = logging.getLogger(__name__)


class CircuitClient(BaseClient):
    """Client for accessing circuit services."""

    def __init__(
            self,
            access_token: str,
            base_url: str,
            **request_kwargs: Any
    ) -> None:
        """CircuitClient constructor.

        Args:
            access_token: IBM Quantum Experience access token.
            base_url: Base URL.
            **request_kwargs: Arguments for the request ``Session``.
        """
        self._session = RetrySession(base_url, access_token, **request_kwargs)
        self.base_api = Api(self._session)

    def list_circuits(self) -> List[Dict[str, Any]]:
        """Return circuits available for this provider.

        Returns:
            Circuits available for this provider.
        """
        return self.base_api.circuits()

    def circuit_get(self, circuit_name: str) -> Dict[str, Any]:
        """Return information about the circuit.

        Args:
            circuit_name: Name of the circuit.

        Returns:
            Circuit information.
        """
        return self.base_api.circuit_adapter(circuit_name).get()

    def circuit_instantiate(
            self,
            circuit_name: str,
            output_format: str,
            **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Instantiate the circuit with the given arguments.

        Args:
            circuit_name: Name of the circuit.
            output_format: Output format.
            **arguments: Arguments used to instantiate the circuit.

        Returns:
            Circuit instance data.
        """
        return self.base_api.circuit_adapter(circuit_name).instantiate(output_format, **arguments)
