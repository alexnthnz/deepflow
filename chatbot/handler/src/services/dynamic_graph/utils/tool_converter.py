"""
Tool Converter

Converts database AvailableTool models to LangChain tools.
"""

import logging
from typing import List, Dict, Any
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, create_model

from database.models import AvailableTool

logger = logging.getLogger(__name__)


class ToolConverter:
    """
    Converts database AvailableTool models to LangChain tools.
    """

    @staticmethod
    def convert_available_tool_to_langchain(tool: AvailableTool) -> StructuredTool:
        """
        Convert an AvailableTool database model to a LangChain StructuredTool.

        Args:
            tool: AvailableTool database model

        Returns:
            StructuredTool: LangChain tool
        """
        try:
            # Extract schema information
            tool_schema = tool.schema

            # Create Pydantic model from schema
            args_schema = ToolConverter._create_pydantic_model_from_schema(
                tool.name, tool_schema
            )

            # Create tool function
            def tool_function(**kwargs):
                # This is a placeholder - in a real implementation,
                # you would route to the actual tool implementation
                logger.info(f"Executing tool {tool.name} with args: {kwargs}")
                return f"Tool {tool.name} executed with args: {kwargs}"

            # Create StructuredTool
            langchain_tool = StructuredTool.from_function(
                func=tool_function,
                name=tool.name,
                description=tool.description or f"Tool: {tool.display_name}",
                args_schema=args_schema,
            )

            return langchain_tool

        except Exception as e:
            logger.error(f"Failed to convert tool {tool.name}: {e}")
            # Return a simple fallback tool
            return StructuredTool.from_function(
                func=lambda: f"Error: Tool {tool.name} conversion failed",
                name=tool.name,
                description=f"Fallback for {tool.display_name}",
            )

    @staticmethod
    def _create_pydantic_model_from_schema(
        tool_name: str, schema: Dict[str, Any]
    ) -> BaseModel:
        """
        Create a Pydantic model from a JSON schema.

        Args:
            tool_name: Name of the tool
            schema: JSON schema dictionary

        Returns:
            BaseModel: Pydantic model class
        """
        try:
            # Extract properties from schema
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            # Build field definitions
            field_definitions = {}
            for field_name, field_schema in properties.items():
                field_type = ToolConverter._get_python_type_from_schema(field_schema)

                # Set default value if not required
                if field_name in required:
                    field_definitions[field_name] = (field_type, ...)
                else:
                    field_definitions[field_name] = (field_type, None)

            # Create dynamic model
            model_name = f"{tool_name.title()}Args"
            return create_model(model_name, **field_definitions)

        except Exception as e:
            logger.warning(f"Failed to create schema for {tool_name}: {e}")
            # Return basic model
            return create_model(f"{tool_name.title()}Args")

    @staticmethod
    def _get_python_type_from_schema(field_schema: Dict[str, Any]):
        """
        Convert JSON schema type to Python type.

        Args:
            field_schema: Field schema dictionary

        Returns:
            Python type
        """
        schema_type = field_schema.get("type", "string")

        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        return type_mapping.get(schema_type, str)

    @staticmethod
    def convert_tools_list(tools: List[AvailableTool]) -> List[StructuredTool]:
        """
        Convert a list of AvailableTool models to LangChain tools.

        Args:
            tools: List of AvailableTool models

        Returns:
            List[StructuredTool]: List of LangChain tools
        """
        converted_tools = []
        for tool in tools:
            try:
                langchain_tool = ToolConverter.convert_available_tool_to_langchain(tool)
                converted_tools.append(langchain_tool)
            except Exception as e:
                logger.error(f"Failed to convert tool {tool.name}: {e}")
                continue

        return converted_tools
