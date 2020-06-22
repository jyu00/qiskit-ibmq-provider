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

"""Test IBMQ circuit service."""

import random
from typing import List, Optional

from qiskit.circuit.quantumcircuit import QuantumCircuit
from qiskit.providers.ibmq.circuits.ibmqcircuit import IBMQCircuit, IBMQCircuitArguments
from qiskit.providers.ibmq.circuits.exceptions import IBMQCircuitNotFound, IBMQCircuitBadArguments
from qiskit.providers.ibmq.api.exceptions import RequestsApiError
from qiskit.providers.ibmq.utils.utils import to_python_identifier

from ..ibmqtestcase import IBMQTestCase
from ..decorators import requires_provider


class TestIBMQCircuit(IBMQTestCase):
    """Test IBMQ circuit service."""

    @classmethod
    @requires_provider
    def setUpClass(cls, provider):
        """Initial class level setup."""
        # pylint: disable=arguments-differ
        super().setUpClass()
        cls.provider = provider

    def test_list_all_circuits(self):
        """Test listing all circuits."""
        circuits = self.provider.circuits()
        self.assertTrue(circuits)
        for circ in circuits:
            self.assertIsInstance(circ, IBMQCircuit)

    def test_get_single_circuit(self):
        """Test retrieving a single circuit."""
        circuit = self.provider.circuits()[0]
        rcircuit = self.provider.get_circuit(circuit.name)
        self.assertIsInstance(rcircuit, IBMQCircuit)
        for arg in rcircuit.arguments:
            self.assertIsInstance(arg, IBMQCircuitArguments)
        self.assertEqual(circuit.name, rcircuit.name)

    def test_get_single_circuit_no_cache(self):
        """Test retrieving a single circuit from the server."""
        circuit_name = self.provider.circuits()[0].name
        # Invalidate the initialized circuits.
        self.provider.circuit._initialized = False
        rcircuit = self.provider.get_circuit(circuit_name)
        self.assertIsInstance(rcircuit, IBMQCircuit)
        self.assertEqual(circuit_name, rcircuit.name)

    def test_get_phantom_circuit(self):
        """Test retrieving a phantom circuit."""
        self.provider.circuits()    # Make sure circuits are initialized.
        with self.assertRaises(IBMQCircuitNotFound) as manager:
            self.provider.get_circuit('phantom_circuit')
        self.assertIn('phantom_circuit', manager.exception.message)

        self.provider.circuit._initialized = False  # Invalidate the initialized circuits.
        with self.assertRaises(RequestsApiError) as manager:
            self.provider.get_circuit('phantom_circuit')
        self.assertIn('phantom_circuit', manager.exception.message)

    def test_referencing_circuit(self):
        """Test referencing a circuit as an attribute."""
        circuit_name = self.provider.circuits()[0].name
        circuit_name_python = to_python_identifier(circuit_name)
        circ = eval('self.provider.circuit.' + circuit_name_python)  # pylint: disable=eval-used
        self.assertIsInstance(circ, IBMQCircuit)
        self.assertEqual(circ.name, circuit_name)

    def test_circuit_instances_refresh(self):
        """Test refreshing circuit service instances."""
        self.provider.circuits()    # Make sure circuits are initialized.
        self.provider.circuit._instances['bad_circuit'] = 'bad_circuit'
        self.provider.circuit.refresh()
        self.assertNotIn('bad_circuit', self.provider.circuit.__dict__)
        self.assertNotIn('bad_circuit', [circ.name for circ in self.provider.circuits()])

    def test_compile_all_args(self):
        """Test compiling a circuit with all arguments"""
        good_circs = [circ for circ in self.provider.circuits() if circ.arguments]
        if not good_circs:
            self.skipTest("Test requires a circuit with arguments.")
        circ = good_circs[random.randrange(len(good_circs))]
        valid_args = {}
        for arg in circ.arguments:
            valid_args[arg.name] = self._get_valid_arg_value(arg)
        compiled_circ = circ.compile(**valid_args)
        self.assertIsInstance(compiled_circ, QuantumCircuit)

    def test_compile_only_required_args(self):
        """Test compiling a circuit with only required arguments."""
        good_circ = None
        for circ in self.provider.circuits():
            args_found = {'required': False, 'optional': False}
            for arg in circ.arguments:
                if arg.required:
                    args_found['required'] = True
                else:
                    args_found['optional'] = True
            if all(args_found.values()):
                good_circ = circ
                break

        if not good_circ:
            self.skipTest("Test requires a circuit with both required and optional arguments.")

        valid_args = {}
        for arg in good_circ.arguments:
            if arg.required:
                valid_args[arg.name] = self._get_valid_arg_value(arg)
        compiled_circ = good_circ.compile(**valid_args)
        self.assertIsInstance(compiled_circ, QuantumCircuit)

    def test_compile_missing_required_args(self):
        """Test compiling a circuit with missing required arguments."""
        good_circ = self._find_arg_type(self.provider.circuits(), True)
        if not good_circ:
            self.skipTest("Test requires a circuit with required arguments.")
        self.assertRaises(IBMQCircuitBadArguments, good_circ.compile())

    def test_compile_invalid_arg_name(self):
        """Test compiling a circuit with an invalid argument name."""
        circuit = self._find_arg_type(self.provider.circuits(), None)
        if not circuit:
            self.skipTest("Test requires a circuit with arguments.")

        with self.assertRaises(IBMQCircuitBadArguments) as manager:
            circuit.compile(phantom_arg='foo')
        self.assertIn('phantom_arg', manager.exception.message)

    def test_compile_invalid_arg_type(self):
        """Test compiling a circuit with an invalid argument type."""
        circuit = self._find_arg_type(self.provider.circuits(), None)
        if not circuit:
            self.skipTest("Test requires a circuit with arguments.")

        bad_args = {}
        for arg in circuit.arguments:
            bad_args[arg.name] = {'life': 42}

        with self.assertRaises(IBMQCircuitBadArguments) as manager:
            circuit.compile(**bad_args)
        self.assertIn('dict', manager.exception.message)

    def _find_arg_type(
            self,
            circuits: List,
            arg_required: Optional[bool]
    ) -> Optional[QuantumCircuit]:
        """Find a circuit with the specified argument requirement.

        Args:
            circuits: A list of circuits to search.
            arg_required: ``True`` if the circuit needs to have at least 1
                required argument. ``False`` if the circuit needs to have at
                least 1 optional argument. ``None`` if the circuit just needs
                to have at least 1 argument.

        Returns:
            A circuit that meets the criteria or ``None``.
        """
        for circ in circuits:
            for arg in circ.arguments:
                if arg_required is None:
                    return circ
                if arg.required == arg_required:
                    return circ
        return None

    def _get_valid_arg_value(self, circ_arg):
        """Return a valid value for the argument type."""
        valid_vars = {"str": "foo",
                      "int": 42,
                      "float": 4.2,
                      "bool": True}
        return valid_vars[circ_arg.type]
