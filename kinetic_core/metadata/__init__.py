"""
Salesforce Metadata API module for kinetic-core.

This module provides support for Salesforce Metadata API operations:
- Retrieve metadata from Salesforce orgs
- Deploy metadata to Salesforce orgs
- Create custom objects and fields
- Manage Salesforce configuration as code

Example:
    >>> from kinetic_core import SalesforceClient
    >>> client = SalesforceClient(session)
    >>>
    >>> # Retrieve metadata
    >>> result = client.metadata.retrieve(
    ...     component_types=["CustomObject", "CustomField"],
    ...     output_dir="./metadata"
    ... )
    >>>
    >>> # Deploy metadata
    >>> result = client.metadata.deploy(
    ...     source_dir="./metadata",
    ...     run_tests=True
    ... )
"""

from kinetic_core.metadata.models import (
    CustomField,
    CustomObject,
    ValidationRule,
    WorkflowRule,
    PicklistValue,
)
from kinetic_core.metadata.client import MetadataClient

__all__ = [
    "MetadataClient",
    "CustomField",
    "CustomObject",
    "ValidationRule",
    "WorkflowRule",
    "PicklistValue",
]
