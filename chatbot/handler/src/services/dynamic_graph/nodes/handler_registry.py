"""
Node Handler Registry

Registry for managing and retrieving node handlers by node type.
"""

import logging
from typing import Dict, Type, Optional
from .base_handler import BaseNodeHandler
from .llm_handler import LLMNodeHandler
from .tool_handler import ToolNodeHandler
from .condition_handler import ConditionNodeHandler
from .human_handler import HumanNodeHandler
from .start_end_handler import StartEndNodeHandler

logger = logging.getLogger(__name__)


class NodeHandlerRegistry:
    """
    Registry for node handlers.

    Manages the mapping between node types and their corresponding
    handler classes.
    """

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self._handlers: Dict[str, Type[BaseNodeHandler]] = {}
        self._instances: Dict[str, BaseNodeHandler] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register the default node handlers."""
        self.register_handler("llm", LLMNodeHandler)
        self.register_handler("tool", ToolNodeHandler)
        self.register_handler("condition", ConditionNodeHandler)
        self.register_handler("human", HumanNodeHandler)
        self.register_handler("start", StartEndNodeHandler)
        self.register_handler("end", StartEndNodeHandler)

    def register_handler(self, node_type: str, handler_class: Type[BaseNodeHandler]):
        """
        Register a node handler for a specific node type.

        Args:
            node_type: Type of node (e.g., 'llm', 'tool', 'condition')
            handler_class: Handler class to register
        """
        self._handlers[node_type] = handler_class
        logger.info(f"Registered handler for node type: {node_type}")

    def get_handler(self, node_type: str) -> Optional[BaseNodeHandler]:
        """
        Get a handler instance for a node type.

        Args:
            node_type: Type of node

        Returns:
            BaseNodeHandler: Handler instance or None if not found
        """
        # Check if we have a cached instance
        if node_type in self._instances:
            return self._instances[node_type]

        # Get handler class
        handler_class = self._handlers.get(node_type)
        if not handler_class:
            logger.warning(f"No handler registered for node type: {node_type}")
            return None

        # Create and cache instance
        try:
            handler_instance = handler_class(self.config_manager)
            self._instances[node_type] = handler_instance
            return handler_instance
        except Exception as e:
            logger.error(f"Failed to create handler for node type {node_type}: {e}")
            return None

    def get_handler_class(self, node_type: str) -> Optional[Type[BaseNodeHandler]]:
        """
        Get the handler class for a node type.

        Args:
            node_type: Type of node

        Returns:
            Type[BaseNodeHandler]: Handler class or None if not found
        """
        return self._handlers.get(node_type)

    def list_handlers(self) -> Dict[str, str]:
        """
        List all registered handlers.

        Returns:
            Dict[str, str]: Mapping of node types to handler class names
        """
        return {
            node_type: handler_class.__name__
            for node_type, handler_class in self._handlers.items()
        }

    def has_handler(self, node_type: str) -> bool:
        """
        Check if a handler is registered for a node type.

        Args:
            node_type: Type of node

        Returns:
            bool: True if handler is registered
        """
        return node_type in self._handlers
