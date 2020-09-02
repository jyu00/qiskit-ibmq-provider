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

import os
import random
from typing import List, Optional

from qiskit import QuantumCircuit
from qiskit.assembler.disassemble import disassemble
from qiskit.providers.ibmq.circuits.circuitdefinition import (CircuitDefinition,
                                                              CircuitParameterDefinition)
from qiskit.providers.ibmq.circuits.exceptions import IBMQCircuitNotFound, IBMQCircuitBadArguments
from qiskit.providers.ibmq.api.exceptions import RequestsApiError
from qiskit.providers.ibmq.utils.utils import to_python_identifier
from qiskit.providers.ibmq.job.ibmqjob import IBMQJob, JobStatus, JOB_FINAL_STATES

from ..ibmqtestcase import IBMQTestCase
from ..decorators import requires_provider


class TestIBMQCircuit(IBMQTestCase):
    """Test IBMQ circuit service."""

    @classmethod
    def setUpClass(cls):
        """Initial class level setup."""
        # pylint: disable=arguments-differ
        super().setUpClass()
        cls.saved_environ = os.environ.get('USE_STAGING_CREDENTIALS')
        os.environ['USE_STAGING_CREDENTIALS'] = 'true'
        cls.provider = cls._setup_provider()    # pylint: disable=no-value-for-parameter
        cls.circuit_definitions = cls.provider.circuit_definitions()

    @classmethod
    def tearDownClass(cls) -> None:
        """Class level tear down."""
        os.environ['USE_STAGING_CREDENTIALS'] = cls.saved_environ

    @classmethod
    @requires_provider
    def _setup_provider(cls, provider):
        """Get the provider for the class."""
        return provider

    def test_list_all_circuits(self):
        """Test listing all circuits."""
        self.assertTrue(self.circuit_definitions)
        for circ in self.circuit_definitions:
            circ.pprint()
            self.assertIsInstance(circ, CircuitDefinition)

    def test_list_all_circuits_family(self):
        """Test listing all circuits with family filter."""
        def _verify_circs(circs, circ_name, q_family):
            found_ref_circ = False
            for circ in circs:
                self.assertIsInstance(circ, CircuitDefinition)
                self.assertEqual(circ.families, q_family)
                if circ.name == circ_name:
                    found_ref_circ = True
            self.assertTrue(found_ref_circ,
                            "Circuit {} not found when query with {}".format(
                                circ_name, q_family))

        ref_circ1 = self.circuit_definitions[0]
        for circ in self.circuit_definitions:
            if len(circ.families) > 1:
                ref_circ1 = circ
                break
        test_families = [(ref_circ1.name, ref_circ1.families)]

        for fam in self.provider.circuit.circuit_families():
            if len(fam.circuits) > 1:
                test_families.append((fam.circuits[0], [fam.name]))
                break

        for circ_name, fam in test_families:
            with self.subTest(family=fam):
                _verify_circs(self.provider.circuit_definitions(family=fam), circ_name, fam)
                self.provider.circuit._initialized = False  # Force querying from server.
                _verify_circs(self.provider.circuit_definitions(family=fam), circ_name, fam)

    def test_get_single_circuit(self):
        """Test retrieving a single circuit."""
        circuit = self.circuit_definitions[0]
        rcircuit = self.provider.circuit_definition(circuit.name)
        self.assertIsInstance(rcircuit, CircuitDefinition)
        for arg in rcircuit.parameters:
            self.assertIsInstance(arg, CircuitParameterDefinition)
        self.assertEqual(circuit.name, rcircuit.name)

    def test_get_single_circuit_no_cache(self):
        """Test retrieving a single circuit from the server."""
        circuit_name = self.circuit_definitions[0].name
        # Invalidate the initialized circuits.
        self.provider.circuit._initialized = False
        rcircuit = self.provider.circuit_definition(circuit_name)
        self.assertIsInstance(rcircuit, CircuitDefinition)
        self.assertEqual(circuit_name, rcircuit.name)

    def test_get_phantom_circuit(self):
        """Test retrieving a phantom circuit."""
        with self.assertRaises(IBMQCircuitNotFound) as manager:
            self.provider.circuit_definition('phantom_circuit')
        self.assertIn('phantom_circuit', manager.exception.message)

        self.provider.circuit._initialized = False  # Invalidate the initialized circuits.
        with self.assertRaises(RequestsApiError) as manager:
            self.provider.circuit_definition('phantom_circuit')
        self.assertIn('phantom_circuit', manager.exception.message)

    def test_referencing_circuit(self):
        """Test referencing a circuit as an attribute."""
        circuit_name = self.circuit_definitions[0].name
        circuit_name_python = to_python_identifier(circuit_name)
        circ = eval('self.provider.circuit.' + circuit_name_python)  # pylint: disable=eval-used
        self.assertIsInstance(circ, CircuitDefinition)
        self.assertEqual(circ.name, circuit_name)

    def test_circuit_instances_refresh(self):
        """Test refreshing circuit service instances."""
        self.provider.circuit._instances['bad_circuit'] = 'bad_circuit'
        self.provider.circuit.refresh()
        self.assertNotIn('bad_circuit', self.provider.circuit.__dict__)
        self.assertNotIn('bad_circuit',
                         [circ.name for circ in self.provider.circuit_definitions()])

    def test_instantiate_missing_required_args(self):
        """Test instantiating a circuit with missing required arguments."""
        circ = self._find_arg_type(self.circuit_definitions, True)
        if not circ:
            self.skipTest("Test requires a circuit with required arguments.")
        with self.assertRaises(IBMQCircuitBadArguments) as manager:
            circ.instantiate()
        self.assertIn('Required parameters', manager.exception.message)

    def test_instantiate_invalid_arg_name(self):
        """Test instantiating a circuit with an invalid argument name."""
        circuit = self._find_arg_type(self.circuit_definitions, None)
        if not circuit:
            self.skipTest("Test requires a circuit with arguments.")

        with self.assertRaises(IBMQCircuitBadArguments) as manager:
            circuit.instantiate(phantom_arg='foo')
        self.assertIn('phantom_arg', manager.exception.message)

    def test_instantiate_opaque_params(self):
        """Test instantiating a remote circuit."""
        circ_def, circ_inst = self._instantiate_circuit_with_params()
        self.assertIsInstance(circ_inst, QuantumCircuit)
        local_qx = QuantumCircuit(circ_inst.num_qubits, circ_inst.num_qubits)
        local_qx.h(0)
        combined_qx = local_qx.compose(circ_inst, qubits=list(range(circ_inst.num_qubits)))
        self.assertIn(circ_def.name, [instr.name for instr, _, _ in combined_qx.data])

        self.assertIn(circ_def.name.lower(), combined_qx.qasm())
        QuantumCircuit.from_qasm_str(combined_qx.qasm())

    def test_execute_lib_circuit(self):
        """Test executing a remote circuit."""
        circ_def = self._get_good_circ()
        valid_args = {}
        for param in circ_def.parameters:
            valid_args[param.name] = self._get_valid_arg_value(param)

        backend = self.provider.backends.ibmq_qasm_simulator
        job = self.provider.circuit.run_remote(
            circuit_name=circ_def.name,
            arguments=valid_args,
            backend=backend,
            shots=1000
        )
        result = job.result()
        self.assertTrue(result.get_counts())

    def test_execute_user_circuits(self):
        """Test executing different user circuits."""
        circ_def, circ_inst = self._instantiate_circuit_with_params()
        local_qx = QuantumCircuit(circ_inst.num_qubits, circ_inst.num_qubits)
        local_qx.h(0)
        local_qx.cx(0, 1)
        combined_qx = local_qx.compose(circ_inst, qubits=list(range(circ_inst.num_qubits)))
        backend = self.provider.backends.ibmq_qasm_simulator

        circ_to_execute = [
            ('remote circuit', circ_inst),
            ('local circuit', local_qx),
            ('combined circuit', combined_qx),
            ('multiple circuit', [circ_inst, combined_qx])]
        for name, circ in circ_to_execute:
            with self.subTest(name=name):
                job = self.provider.circuit.run(
                    circ, backend=backend, shots=2048)
                self.assertTrue(isinstance(job, IBMQJob))
                job.result()
                qobj = job.qobj()
                rqx, rconfig, _ = disassemble(qobj)
                self.assertEqual(rconfig['shots'], 2048)

    def test_circuit_families(self):
        """Test querying for circuit families."""
        families = self.provider.circuit.circuit_families()
        family_names = [fam.name for fam in families]
        known_families = [family for circ_def in self.circuit_definitions
                          for family in circ_def.families]
        self.assertTrue(all(fam in family_names for fam in known_families),
                        "retrieved family names: {}, known families: {}".format(
                            family_names, known_families))

    def _find_arg_type(
            self,
            circuits: List,
            arg_required: Optional[bool]
    ) -> Optional[CircuitDefinition]:
        """Find a circuit with the specified argument requirement.

        Args:
            circuits: A list of circuits to search.
            arg_required: ``True`` if the circuit needs to have at least 1
                required argument. ``False`` if the circuit needs to have at
                least 1 optional argument. ``None`` if the circuit just needs
                to have at least 1 argument.

        Returns:
            A circuit definition that meets the criteria or ``None``.
        """
        for circ in circuits:
            for arg in circ.parameters:
                if arg_required is None:
                    return circ
                if arg.required == arg_required:
                    return circ
        return None

    def _get_valid_arg_value(self, circ_arg):
        """Return a valid value for the argument type."""
        valid_vars = {"str": "foo",
                      "int": 5,
                      "float": 4.2,
                      "bool": True,
                      "array[int]": [1, -1, -1, -1]
                      }
        return valid_vars[circ_arg.type]

    def _instantiate_circuit_with_params(self):
        """Instantiate a circuit with parameters."""
        circ = self._get_good_circ()
        valid_args = {}
        for param in circ.parameters:
            valid_args[param.name] = self._get_valid_arg_value(param)
        self.log.info("Using circuit {} with parameters {}".format(circ.name, valid_args))
        circ_inst = circ.instantiate(**valid_args)
        return circ, circ_inst

    def _get_good_circ(self):
        """Get a list of circuits that can be easily instantiated."""
        good_circ_names = ['QFT', 'FourierChecking', 'QuantumVolume', 'InnerProduct',
                           'PhaseEstimation']
        good_circs = [circ for circ in self.circuit_definitions if circ.name in good_circ_names]
        circ = good_circs[random.randrange(len(good_circs))]
        return circ
