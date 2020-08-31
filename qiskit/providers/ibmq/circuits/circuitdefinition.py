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

"""IBM Quantum Experience circuit."""

import logging
import inspect
from typing import Dict, Any, List

from qiskit.circuit.quantumcircuit import QuantumCircuit
from qiskit.providers.ibmq import accountprovider  # pylint: disable=unused-import
import qiskit.circuit.library as circuit_library
from qiskit.circuit.exceptions import CircuitError

from .exceptions import IBMQCircuitBadArguments, CircuitReferenceNotFound
from .remotegate import RemoteGate
from ..api.clients.circuit import CircuitClient

logger = logging.getLogger(__name__)


class CircuitDefinition:
    """An circuit definition instance."""

    def __init__(
            self,
            provider: 'accountprovider.AccountProvider',
            api_client: CircuitClient,
            name: str,
            description: str,
            arguments: List[Dict[str, Any]],
            families: List[str]
    ):
        """CircuitDefinition constructor.

        Args:
            provider: Provider for this circuit.
            api_client: Client for accessing the API.
            name: Circuit name.
            description: Circuit description.
            arguments: A list of parameters for the circuit.
            families: A list of families the circuit belongs to.
        """
        self._provider = provider
        self._api_client = api_client
        self._name = name
        self._description = description
        self._parameters = [CircuitParameterDefinition.from_dict(raw_arg) for raw_arg in arguments]
        self._families = families

    def instantiate(self, **kwargs: Any) -> QuantumCircuit:
        """Instantiate the circuit with the input arguments.

        Args:
            **kwargs: Arguments used to instantiate the circuit.

        Returns:
            A :class:`QuantumCircuit` instantiated using the input arguments.

        Raises:
            IBMQCircuitBadArguments: If an input argument is not valid.
            ApiIBMQProtocolError: If invalid data received from the server.
            CircuitReferenceNotFound: If a local reference circuit cannot be found.
        """
        # Check for extra parameters.
        param_names = [param.name for param in self.parameters]
        extra_params = [user_param for user_param in kwargs if user_param not in param_names]
        if extra_params:
            raise IBMQCircuitBadArguments(
                "{} are not valid parameters for {}".format(','.join(extra_params), self.name))

        # Check for missing parameters.
        missing_params = [param.name for param in self.parameters
                          if param.required and param.name not in kwargs]
        if missing_params:
            raise IBMQCircuitBadArguments(
                "Required parameters {} are missing.".format(','.join(missing_params)))

        circ_lib = inspect.getmembers(circuit_library, inspect.isclass)
        circ_class = None
        for lib_elem in circ_lib:
            if lib_elem[0].lower() == self.name.lower():
                circ_class = lib_elem[1]
                break

        if not circ_class:
            raise CircuitReferenceNotFound(
                "Unable to find a reference {} circuit in circuit library.".format(self.name))

        try:
            ref_qx = circ_class(**kwargs)
        except CircuitError as cerr:
            raise IBMQCircuitBadArguments(str(cerr)) from None
        opaque_gate = RemoteGate(name=self.name, num_qubits=ref_qx.num_qubits, params=[])
        opaque_gate._is_remote = True
        opaque_gate._remote_params = ["{}={}".format(name, val) for name, val in kwargs.items()]
        out_qx = QuantumCircuit(*ref_qx.qregs)
        out_qx.append(opaque_gate, list(range(ref_qx.num_qubits)))
        return out_qx

    def pprint(self) -> None:
        """Print a formatted description of this circuit."""
        formatted = '{}: {}\n  Provider: {}'.format(
            self.name, self.description, self.provider)
        if self.parameters:
            formatted += '\n  Parameters:'
            for param in self.parameters:
                required = 'Required.' if param.required else ''
                formatted += '\n    {} ({}): {}. {}'.format(
                    param.name, param.type, param.description, required)
        if self.families:
            formatted += '\n  Families: ' + ', '.join(self.families)
        print(formatted)

    @property
    def provider(self):
        """Return the provider."""
        return self._provider

    @property
    def name(self):
        """Return name of the circuit."""
        return self._name

    @property
    def description(self):
        """Return description of the circuit."""
        return self._description

    @property
    def parameters(self):
        """Return parameter definitions for the circuit."""
        return self._parameters

    @property
    def families(self):
        """Return families of the circuit."""
        return self._families

    def __repr__(self) -> str:
        return "<{}('{}') from {}>".format(self.__class__.__name__,
                                           self.name,
                                           self.provider)

    def __str__(self) -> str:
        return "{}: {}. Parameters: {}".format(
            self.name, self.description, ', '.join([param.name for param in self.parameters]))


class CircuitParameterDefinition:
    """Parameters for an IBM Quantum Experience circuit."""

    def __init__(self, name: str, description: str, type: str, required: str) -> None:
        """CircuitParameterDefinition constructor.

        Args:
            name: Name of the parameter.
            description: Description of the parameter.
            type: Parameter type.
            required: Whether the parameter is required.
        """
        # pylint: disable=redefined-builtin
        self.name = name
        self.description = description
        self.type = type
        self.required = required

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CircuitParameterDefinition':
        """Return an instance of this class based on input data.

        Args:
            data: Data used to construct the class.

        Returns:
            An instance of this class based on input data
        """
        return cls(**data)

    def __str__(self) -> str:
        return "{}: {}. Type={}, Required={}".format(
            self.name, self.description, self.type, self.required)