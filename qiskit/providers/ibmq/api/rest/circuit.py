# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2018, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Circuit REST adapter."""

import logging
from typing import Dict, Any, List, Optional
import json
import os

from .base import RestAdapterBase
from ..session import RetrySession

logger = logging.getLogger(__name__)


class Circuit(RestAdapterBase):
    """Rest adapter for circuit related endpoints."""

    URL_MAP = {
        'self': '',
        'compile': '/compiled'
    }

    def __init__(self, session: RetrySession, circuit_name: Optional[str]) -> None:
        """Circuit constructor.

        Args:
            session: Session to be used in the adapter.
            circuit_name: Name of the circuit.
        """
        self.base_url = os.getenv('QE_CIRCUIT_URL')
        self._circuit_name = circuit_name
        url_prefix = '/circuits/{}'.format(circuit_name) if circuit_name else '/circuits'
        super().__init__(session, url_prefix)

    def get(self) -> Dict[str, Any]:
        """Return circuit information.

        Returns:
            JSON response of circuit information.
        """
        url = self.get_url('self')
        return self.session.get(url, bare=True).json()

    def compile(self, output_format: str, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Compile the circuit with the input arguments.

        Args:
            output_format: Output format.
            **arguments: Arguments used to compile the circuit.

        Returns:
            JSON response of the compiled circuit information.
        """
        url = self.get_url('compile')
        params = {
            'arguments': json.dumps(arguments),
            'output_format': output_format
        }
        response = self.session.get(url, params=params, bare=True).json()
        return response

    def circuits(self) -> List[Dict[str, Any]]:
        """Return a list of circuits.

        Returns:
            JSON response.
        """
        url = self.get_url('self')
        return self.session.get(url, bare=True).json()

    def get_url(self, identifier: str) -> str:
        """Return the resolved URL for the specified identifier.

        Args:
            identifier: Internal identifier of the endpoint.

        Returns:
            The resolved URL of the endpoint (relative to the session base URL).
        """
        return '{}{}'.format(self.base_url + self.prefix_url, self.URL_MAP[identifier])
