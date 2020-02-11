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

import logging
import json

logger = logging.getLogger(__name__)


class GateDefinition:
    """Gate definition."""

    def __init__(self, gate_definition=None, merge=False, filename=None):
        """Create a new gate definition.

        Args:
            gate_definition: Gate definition dictionary. The key of the
                dictionary is the gate and the qubits, separated by blanks.
                The value is another dictionary, whose key is the logical
                    channel and value is the mapping.
        """

        self._data = gate_definition or {}
        self._control = {'merge': merge}
        if filename:
            self.load(filename)

    def merge_default(self, merge=False):
        """

        Args:
            merge: if True, this gate definition will be merged with the
                default gate definition. Otherwise this gate definition will
                replace the default.
        """
        self._control['merge'] = merge

    def add(self, gate, qubits, mapping):
        """Add another entry in the gate definition.

        Args:
            gate: Gate to be mapped.
            qubits: Qubits to be mapped.
            mapping: A dictionary whose key is the logical channel, and value
                is the mapping.
        """
        gate_qubit = '{} {}'.format(gate, ' '.join([str(x) for x in qubits]))
        self._data[gate_qubit] = mapping

    def load(self, filename):
        """Load gate definition from the file.

        Args:
            filename: Name of the file to load the gate definition from.
        """
        with open(filename, 'r') as gate_def_file:
            self._data = json.load(gate_def_file)

    def save(self, filename):
        """Save current gate definition to a file.

        Args:
            filename: Name of the file to load the gate definition from.
        """
        with open(filename, 'w') as gate_def_file:
            json.dump(self._data, gate_def_file)

    def to_dict(self):
        """Return this gate definition in a dictionary format.

        Returns:
            This gate definition as a dictionary.
        """
        return self._data

    @classmethod
    def from_dict(cls, data):
        """Return a GateDefinition instance from the input data."""
        return cls(data)

    def get_control(self):
        """Return control information."""
        return self._control

    def __repr__(self):
        return str(self._data)
