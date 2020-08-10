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

"""This module implements the abstract base class for service modules.

To create an add-on service module, subclass the IBMQService class in this
module and implement the required methods.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

from qiskit.providers.ibmq import accountprovider  # pylint: disable=unused-import

from .utils.utils import to_python_identifier
from .api.exceptions import RequestsApiError

logger = logging.getLogger(__name__)


class IBMQService(ABC):
    """Base class for services."""

    _service_name = 'service'

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
        self._provider = provider
        self._access_token = access_token
        self._instances = {}  # type: Dict[str, Any]
        self._initialized = False

    def _discover_instances(self) -> None:
        """Discovers the remote service instances, if not already known."""
        if not self._initialized:
            self._delete_all_instances()
            try:
                for raw_config in self._list_instances():
                    if not isinstance(raw_config, dict):
                        logger.warning("An error occurred when retrieving %s information."
                                       " Some %s instances might not be available.",
                                       self._service_name, self._service_name)
                        continue
                    inst_id, instance = self._to_service_instance(raw_config)
                    self._instances[inst_id] = instance
                self.__dict__.update(self._instances)
            except RequestsApiError as err:
                logger.warning("Unable to retrieve %s information. "
                               "Please try again later. Error: %s: %s", self._service_name,
                               str(type(err)), err)
                return

            self._initialized = True

    def _add_instance(self, inst_id: Any, instance: Any) -> None:
        """Add a service instance.

        Args:
            inst_id: Instance ID.
            instance: Service instance.
        """
        self._instances[inst_id] = instance
        self.__dict__[inst_id] = instance

    def _delete_all_instances(self) -> None:
        """Delete all service instances."""
        for inst in self._instances:
            self.__dict__.pop(inst, None)
        self._instances = {}

    @abstractmethod
    def _list_instances(self) -> List[Dict[str, Any]]:
        """Discover remote service instances accessible via this provider.

        Returns:
            Raw data containing a list of service instances.
        """
        pass

    @abstractmethod
    def _to_service_instance(self, raw_data: Dict[str, Any]) -> Tuple[str, Any]:
        """Convert the raw data returned from the server to a service instance.

        Args:
            raw_data: Raw data returned from the server.

        Returns:
            A tuple of the service instance ID and the instance. The ID must be a
            unique and valid Python identifier.
        """
        pass

    def _to_unique_python_identifier(self, instance_id: str) -> str:
        """Convert the service instance ID to a unique Python identifier.

        Args:
            instance_id: Instance ID.

        Returns:
            A unique Python identifier for the instance.
        """
        inst_python_id = to_python_identifier(instance_id)
        # Append _ if duplicate
        while inst_python_id in self._instances:
            inst_python_id += '_'
        return inst_python_id

    def refresh(self) -> None:
        """Rediscover service instances."""
        self._initialized = False
        self._discover_instances()

    def instances(self) -> List[Any]:
        """Return all instances for this service."""
        self._discover_instances()
        return list(self._instances.values())

    @abstractmethod
    def get_instance(self, **kwargs: Any) -> Any:
        """Return a specific service instance."""
        pass

    def __dir__(self) -> Dict:
        self._discover_instances()
        return self.__dict__

    def __getattr__(self, item: Any) -> Any:
        self._discover_instances()
        try:
            return self._instances[item]
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'".format(
                self.__class__.__name__, item))
