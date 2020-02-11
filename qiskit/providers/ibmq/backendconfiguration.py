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
from typing import Dict, List, Callable, Optional, Any, Union
from types import SimpleNamespace

logger = logging.getLogger(__name__)


class BackendConfiguration(SimpleNamespace):
    """IBMQ Backend configuration."""

    def __init__(self, gate_def=None, shots=None):
        self.gate_def = gate_def
        self.shots = shots

        super().__init__()

    def set_config(self, gate_def=None, shots=None):
        """Set new configuration.

        Args:
            gate_def: Gate definition.
            shots: Shots.
        """
        self.gate_def = gate_def or self.gate_def
        self.shots = shots or self.shots
