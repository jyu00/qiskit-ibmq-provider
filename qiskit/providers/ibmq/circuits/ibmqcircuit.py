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
from typing import Dict, Any, List

from qiskit.circuit.quantumcircuit import QuantumCircuit

from .apiconstants import CircuitOutputType
from .exceptions import IBMQCircuitBadArguments
from ..api.exceptions import ApiIBMQProtocolError

logger = logging.getLogger(__name__)


class IBMQCircuit:
    """An IBM Quantum Experience circuit instance."""

    def __init__(self, provider, name, description: str, arguments: List[Dict[str, Any]]):
        """IBMQCircuit constructor.

        Args:
            provider: Provider for this circuit.
            name: Circuit name.
            description: Circuit description.
            arguments: A list of arguments for the circuit.
        """
        self.provider = provider
        self._api = provider._api
        self.name = name
        self.description = description
        self.arguments = [IBMQCircuitArguments.from_dict(arg) for arg in arguments]

    def compile(self, **kwargs) -> QuantumCircuit:
        """Compile the circuit.

        Args:
            **kwargs: Arguments used to compile the circuit.

        Returns:
            Compiled circuit.

        Raises:
            IBMQCircuitBadArguments: If an input argument is not valid.
        """
        # Check for extra arguments.
        arg_names = [arg.name for arg in self.arguments]
        extra_args = [user_arg for user_arg in kwargs if user_arg not in arg_names]
        if extra_args:
            raise IBMQCircuitBadArguments(
                "{} are not valid arguments for {}".format(','.join(extra_args), self.name))

        # Check for missing arguments.
        missing_args = [arg.name for arg in self.arguments
                        if arg.required and arg.name not in kwargs]
        if missing_args:
            raise IBMQCircuitBadArguments(
                "Required arguments {} are missing.".format(','.join(missing_args)))

        # TODO
        # Verify argument types.

        raw_response = self._api.circuit_compile(self.name, CircuitOutputType.QASM, **kwargs)
        if raw_response['format'] != CircuitOutputType.QASM:
            raise ApiIBMQProtocolError("Invalid output format {} received from "
                                       "the server.".format(raw_response['format']))
        return QuantumCircuit.from_qasm_str(raw_response['circuit'])

    def __repr__(self):
        return "<{}('{}') from {}>".format(self.__class__.__name__,
                                           self.name,
                                           self.provider)

    def __str__(self):
        return "{}: {}".format(self.name, self.description)


class IBMQCircuitArguments:
    """Arguments for an IBM Quantum Experience circuit."""

    def __init__(self, name: str, description: str, type: str, required: str):
        """

        Args:
            name: Name of the argument.
            description: Description of the argument.
            type: Argument type.
            required: Whether the argument is required.
        """
        self.name = name
        self.description = description
        self.type = type
        self.required = required

    @classmethod
    def from_dict(cls, data):
        """Return an instance of this class based on input data.

        Args:
            data: Data used to construct the class.

        Returns:
            An instance of this class based on input data
        """
        return cls(**data)

    def __str__(self):
        return "{}: {}. Type={}, Required={}".format(
            self.name, self.description, self.type, self.required)
