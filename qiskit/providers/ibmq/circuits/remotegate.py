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

"""Remote gate."""

from typing import List, Optional

from qiskit.circuit.gate import Gate


class RemoteGate(Gate):
    """Remote gate."""

    def __init__(self, name: str, num_qubits: int, params: List,
                 label: Optional[str] = None) -> None:
        """Create a new remote gate.

        Args:
            name: The Qobj name of the gate.
            num_qubits: The number of qubits the gate acts on.
            params: A list of parameters.
            label: An optional label for the gate.
        """
        super().__init__(name, num_qubits, params=[], label=label)
        self._remote_params = params
        self._is_remote = True
        self.label = 'remote_' + name

    def qasm(self) -> str:
        """Return a default OpenQASM string for the gate.

        Returns:
            OpenQASM string for the gate.
        """
        qasm_remote = '// PRAGMA remote-circuit {}({})'.format(
            self.name, ','.join(self._remote_params))
        qasm_remote += '\nopaque {} {};'.format(
            self.name.lower(), ','.join(["q"+str(digit) for digit in range(self.num_qubits)]))
        qasm_remote += '\n// PRAGMA remote-circuit'
        qasm_remote += '\n{}'.format(self.name.lower())
        return qasm_remote
