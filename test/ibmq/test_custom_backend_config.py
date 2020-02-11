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

"""BackendConfiguration Test."""

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.compiler import assemble, transpile
from qiskit.providers.ibmq.backendconfiguration import BackendConfiguration
from qiskit.providers.ibmq.gatedefinition import GateDefinition

from ..ibmqtestcase import IBMQTestCase
from ..decorators import requires_provider


class TestBackendConfiguration(IBMQTestCase):
    """Test ibmqbackend module."""

    @requires_provider
    def test_custom_gatedef(self, provider):
        """Test using a custom gate definition."""
        backend = provider.get_backend('ibmq_olympus')

        qx = QuantumCircuit(2, 2)
        qx.x(0)
        qx.cx(0, 1)
        qx.measure([0, 1], [0, 1])
        qobj = assemble(transpile(qx, backend=backend), backend=backend)

        gate_def = GateDefinition()
        gate_def.add(gate='cx', qubits=[0, 1], mapping={
            'Q0': 'X90p;',
            'Q1': 'X90p;',
            'CR0_1': 'CR90p;'})
        for qubit in range(2):
            gate_def.add(gate='x', qubits=[qubit], mapping={'Q%d' % qubit: 'Yp;'})
            gate_def.add(gate='u3 @ @ @', qubits=[qubit], mapping={'Q%d' % qubit: 'Yp;'})
            gate_def.add(gate='MEAS', qubits=[qubit], mapping={
                'Q%d' % qubit: '|meas;',
                'M%d' % qubit: '|meas; M;'
            })
        gate_def.merge_default(False)
        my_config = BackendConfiguration(gate_def=gate_def)
        backend.set_custom_config(my_config)

        # job = backend.run(qobj)
        # job.result()
        rjob = backend.retrieve_job('5e42e1458c83b10011e305ea')
        # rjob = backend.retrieve_job(job_id=job.job_id())
        from pprint import pprint
        print(f"Backend configuration used is:")
        pprint(rjob.backend_configuration().gate_def.to_dict())


def _bell_circuit():
    qr = QuantumRegister(2, 'q')
    cr = ClassicalRegister(2, 'c')
    qc = QuantumCircuit(qr, cr)
    qc.h(qr[0])
    qc.cx(qr[0], qr[1])
    qc.measure(qr, cr)
    return qc
