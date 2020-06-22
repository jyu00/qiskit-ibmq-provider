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
from qiskit.providers.ibmq import accountprovider  # pylint: disable=unused-import

from .apiconstants import CircuitOutputType
from .exceptions import IBMQCircuitBadArguments
from ..api.exceptions import ApiIBMQProtocolError

logger = logging.getLogger(__name__)


class IBMQCircuit:
    """An IBM Quantum Experience circuit instance."""

    def __init__(
            self,
            provider: 'accountprovider.AccountProvider',
            name: str,
            description: str,
            arguments: List[Dict[str, Any]]
    ):
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
        self.arguments = [IBMQCircuitArguments.from_dict(raw_arg) for raw_arg in arguments]

    def compile(self, **kwargs: Any) -> QuantumCircuit:
        """Compile the circuit.

        Args:
            **kwargs: Arguments used to compile the circuit.

        Returns:
            Compiled circuit.

        Raises:
            IBMQCircuitBadArguments: If an input argument is not valid.
            ApiIBMQProtocolError: If invalid data received from the server.
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

        # Verify argument types.
        arg_dict = {arg.name: arg for arg in self.arguments}
        for user_arg_name, user_arg in kwargs.items():
            try:
                arg_type = eval(arg_dict[user_arg_name].type)   # pylint: disable=eval-used
                if not isinstance(user_arg, arg_type):
                    raise IBMQCircuitBadArguments("Argument {} should be type {}, not {}".format(
                        user_arg_name, arg_type, type(user_arg)))
            except AttributeError:
                pass

        raw_response = self._api.circuit_compile(self.name, CircuitOutputType.QASM, **kwargs)
        if raw_response['format'] != CircuitOutputType.QASM:
            raise ApiIBMQProtocolError("Invalid output format {} received from "
                                       "the server.".format(raw_response['format']))
        return QuantumCircuit.from_qasm_str(raw_response['circuit'])

    def pprint(self):
        """Print a formatted description of this circuit."""
        formatted = '{}: {}\n  Provider: {}'.format(
            self.name, self.description, self.provider)
        if self.arguments:
            formatted += '\n  Arguments:'
            for arg in self.arguments:
                required = 'Required.' if arg.required else ''
                formatted += '\n    {} ({}): {}. {}'.format(
                    arg.name, arg.type, arg.description, required)
        print(formatted)

    def __repr__(self) -> str:
        return "<{}('{}') from {}>".format(self.__class__.__name__,
                                           self.name,
                                           self.provider)

    def __str__(self) -> str:
        return "{}: {}. Arguments: {}".format(
            self.name, self.description, ', '.join([arg.name for arg in self.arguments]))


class IBMQCircuitArguments:
    """Arguments for an IBM Quantum Experience circuit."""

    def __init__(self, name: str, description: str, type: str, required: str) -> None:
        """IBMQCircuitArguments constructor.

        Args:
            name: Name of the argument.
            description: Description of the argument.
            type: Argument type.
            required: Whether the argument is required.
        """
        # pylint: disable=redefined-builtin
        self.name = name
        self.description = description
        self.type = type
        self.required = required

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IBMQCircuitArguments':
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
