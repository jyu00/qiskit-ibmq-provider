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

import os
import logging
from typing import List, Any, Dict, Tuple, Optional, Union
import uuid

from qiskit import QuantumCircuit

from .circuitdefinition import CircuitDefinition
from .exceptions import IBMQCircuitNotFound
from ..ibmqservice import IBMQService
from ..api.clients.circuit import CircuitClient
from ..job.ibmqjob import IBMQJob
from ..ibmqbackend import IBMQBackend


logger = logging.getLogger(__name__)


class CircuitService(IBMQService):
    """Circuit related services."""

    _service_name = 'circuit'

    def __init__(
            self,
            provider: 'accountprovider.AccountProvider',
            access_token: str
    ) -> None:
        """Base class for services.

        Args:
            provider: Provider responsible for this service.
            access_token: IBM Quantum Experience access token.
        """
        super().__init__(provider, access_token)
        # TODO Get base url from API
        base_url = os.getenv('QE_CIRCUIT_URL')
        credentials = self._provider.credentials
        self._api_client = CircuitClient(access_token, base_url,
                                         **credentials.connection_parameters())

    def _list_instances(self) -> List[Dict[str, Any]]:
        """Discover remote circuit instances accessible via this service.

        Returns:
            Raw data containing a list of circuit instances.
        """
        return self._api_client.list_circuits()

    def _to_service_instance(self, raw_data: Dict[str, Any]) -> Tuple[str, CircuitDefinition]:
        """Convert the raw data returned from the server to a circuit instance.

        Args:
            raw_data: Raw data returned from the server.

        Returns:
            A tuple of the circuit ID and circuit instance.
        """
        circ_id = self._to_unique_python_identifier(raw_data['name'])
        return circ_id, CircuitDefinition(
            provider=self._provider,
            api_client=self._api_client,
            **raw_data)

    def get_instance(self, name: str) -> CircuitDefinition:  # type: ignore[override]
        """Return a specific circuit definition.

        Args:
            name: Name of the circuit.

        Returns:
            Definition of the named circuit.

        Raises:
            IBMQCircuitNotFound: If the circuit is not found.
        """
        # pylint: disable=arguments-differ
        if self._initialized:
            for circ in self.instances():
                if circ.name == name:
                    return circ
            raise IBMQCircuitNotFound(
                "Circuit {} is not available with this provider.".format(name))

        # TODO Catch circuit not found error if possible.
        # Retrieve a single circuit.
        circ_id, circ = self._to_service_instance(self._api_client.circuit_get(name))
        self._add_instance(circ_id, circ)
        return circ

    def run(
            self,
            circuits: Union[QuantumCircuit, List[QuantumCircuit]],
            backend: IBMQBackend,
            shots: int = 1024,
            qobj_header: Optional[dict] = None
    ) -> IBMQJob:
        """

        Args:
            circuits: The circuits to execute.
            backend: Backend to submit the circuits to.
            shots: Number of repetitions of each circuit.
            qobj_header: User input that will be inserted in Qobj header,
                and will also be copied to the corresponding :class:`qiskit.result.Result`
                header. Headers do not affect the run.

        Returns:

        """
        if isinstance(circuits, QuantumCircuit):
            circuits = [circuits]
        qasm_strs = []
        for circ in circuits:
            init_qasm = circ.qasm().split('\n')
            final_qasm = []
            opaque_gates = []
            for index, line in enumerate(init_qasm):
                # Remove duplicate opaque gate.
                if line.startswith('opaque') and \
                        init_qasm[index-1].startswith('// PRAGMA remote-circuit'):
                    gate_name = line.split()[1]
                    if gate_name in opaque_gates:
                        continue
                    opaque_gates.append(gate_name)
                final_qasm.append(line)
            qasm_strs.append('\n'.join(final_qasm))
            print('\n'.join(final_qasm))

        qobj_header = qobj_header or {}
        qobj_header = {**dict(backend_name=backend.name(),
                              backend_version=backend.configuration().backend_version),
                       **qobj_header}

        payload = {     # pylint: disable=unused-variable
            "experiments": qasm_strs,
            "header": qobj_header,
            "config": {"shots": shots},
            "qobj_id": str(uuid.uuid4()),
            "schema_version": "1.2.0"
        }
