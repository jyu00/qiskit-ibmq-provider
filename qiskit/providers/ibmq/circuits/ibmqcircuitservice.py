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

"""Circuit services."""

import logging
from typing import List, Any, Dict, Tuple

from ..ibmqservice import IBMQService
from .ibmqcircuit import IBMQCircuit
from .exceptions import IBMQCircuitNotFound

logger = logging.getLogger(__name__)


class IBMQCircuitService(IBMQService):
    """Circuit related services."""

    _service_name = 'circuit'

    def _list_instances(self) -> List[Dict[str, Any]]:
        """Discover remote circuit instances accessible via this service.

        Returns:
            Raw data containing a list of circuit instances.
        """
        return self._api.list_circuits()

    def _to_service_instance(self, raw_data: Dict[str, Any]) -> Tuple[str, IBMQCircuit]:
        """Convert the raw data returned from the server to a circuit instance.

        Args:
            raw_data: Raw data returned from the server.

        Returns:
            A tuple of the circuit ID and circuit instance.
        """
        circ_id = self._to_unique_python_identifier(raw_data['name'])
        return circ_id, IBMQCircuit(provider=self._provider, **raw_data)

    def get_instance(self, name: str) -> IBMQCircuit:
        """Return a specific circuit.

        Args:
            name: Name of the circuit.

        Returns:
            The named circuit.

        Raises:
            IBMQCircuitNotFound: If the circuit is not found.
        """
        if self._initialized:
            for circ in self.instances():
                if circ.name == name:
                    return circ
            raise IBMQCircuitNotFound(
                "Circuit {} is not available with this provider.".format(name))

        # TODO Catch circuit not found error if possible.
        # Retrieve a single circuit.
        circ_id, circ = self._to_service_instance(self._api.circuit_get(name))
        self._add_instance(circ_id, circ)
        return circ
