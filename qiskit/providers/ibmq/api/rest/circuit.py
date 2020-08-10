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
from typing import Dict, Any
import json

from .base import RestAdapterBase
from ..session import RetrySession

logger = logging.getLogger(__name__)


class Circuit(RestAdapterBase):
    """Rest adapter for circuit related endpoints."""

    URL_MAP = {
        'self': '',
        'compile': '/compiled'
    }

    def __init__(self, session: RetrySession, circuit_name: str) -> None:
        """Circuit constructor.

        Args:
            session: Session to be used in the adapter.
            circuit_name: Name of the circuit.
        """
        url_prefix = '/circuits/{}'.format(circuit_name)
        super().__init__(session, url_prefix)

    def get(self) -> Dict[str, Any]:
        """Return circuit information.

        Returns:
            JSON response of circuit information.
        """
        url = self.get_url('self')
        return self.session.get(url).json()

    def instantiate(self, output_format: str, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Instantiate the circuit with the input arguments.

        Args:
            output_format: Output format.
            **arguments: Arguments used to instantiate the circuit.

        Returns:
            JSON response of the circuit information.
        """
        url = self.get_url('compile')
        params = {
            'arguments': json.dumps(arguments),
            'output_format': output_format
        }
        response = self.session.get(url, params=params).json()
        return response
