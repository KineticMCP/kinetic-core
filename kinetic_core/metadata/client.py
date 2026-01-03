"""
Salesforce Metadata API client.

Provides high-level interface for Metadata API operations:
- Retrieve metadata from orgs
- Deploy metadata to orgs
- Create/update custom objects and fields
"""

import os
import zipfile
import io
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from kinetic_core.core.session import SalesforceSession
from kinetic_core.metadata.models import (
    CustomField,
    CustomObject,
    DeployResult,
    RetrieveResult,
)
from kinetic_core.metadata.xml_builder import (
    custom_field_to_xml,
    custom_object_to_xml,
    create_package_xml,
)
from kinetic_core.metadata.xml_parser import (
    parse_custom_field,
    parse_custom_object,
    parse_package_xml,
)


class MetadataClient:
    """
    Client for Salesforce Metadata API operations.

    This client provides methods to:
    - Retrieve metadata from Salesforce orgs
    - Deploy metadata to Salesforce orgs
    - Create custom fields and objects
    - Compare metadata between orgs

    Example:
        >>> from kinetic_core import SalesforceClient
        >>> client = SalesforceClient(session)
        >>>
        >>> # Retrieve metadata
        >>> result = client.metadata.retrieve(
        ...     component_types=["CustomObject"],
        ...     output_dir="./metadata"
        ... )
        >>>
        >>> # Deploy a field
        >>> field = CustomField(
        ...     sobject="Account",
        ...     name="Customer_Tier__c",
        ...     type=FieldType.TEXT,
        ...     label="Customer Tier",
        ...     length=50
        ... )
        >>> result = client.metadata.deploy_field(field)
    """

    def __init__(self, session: SalesforceSession):
        """
        Initialize MetadataClient.

        Args:
            session: Authenticated Salesforce session
        """
        self.session = session
        self.base_url = f"{session.instance_url}/services/Soap/m/{session.api_version}"
        self.metadata_url = f"{session.instance_url}/services/Soap/m/{session.api_version}"

    def describe_metadata(self, api_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve metadata types available in the org.

        Args:
            api_version: API version to use (defaults to session version)

        Returns:
            Dictionary with metadata types and their properties

        Example:
            >>> types = client.metadata.describe_metadata()
            >>> print(f"Available types: {len(types['metadataObjects'])}")
        """
        # TODO: Implement SOAP call to describeMetadata
        # For now, return a stub with common types
        return {
            "organizationNamespace": "",
            "partialSaveAllowed": True,
            "testRequired": False,
            "metadataObjects": [
                {"directoryName": "objects", "xmlName": "CustomObject"},
                {"directoryName": "fields", "xmlName": "CustomField"},
                {"directoryName": "validationRules", "xmlName": "ValidationRule"},
                {"directoryName": "workflows", "xmlName": "WorkflowRule"},
            ]
        }

    def retrieve(
        self,
        component_types: List[str],
        output_dir: str,
        specific_components: Optional[Dict[str, List[str]]] = None,
        api_version: Optional[str] = None,
    ) -> RetrieveResult:
        """
        Retrieve metadata from Salesforce org.

        Args:
            component_types: List of metadata types to retrieve
                           (e.g., ["CustomObject", "CustomField"])
            output_dir: Directory to extract retrieved metadata
            specific_components: Optional dict mapping type to specific members.
                               If None, retrieves all (*) for each type.
            api_version: API version (defaults to session version)

        Returns:
            RetrieveResult with status and file properties

        Example:
            >>> # Retrieve all custom objects
            >>> result = client.metadata.retrieve(
            ...     component_types=["CustomObject"],
            ...     output_dir="./metadata"
            ... )
            >>>
            >>> # Retrieve specific objects
            >>> result = client.metadata.retrieve(
            ...     component_types=["CustomObject"],
            ...     output_dir="./metadata",
            ...     specific_components={
            ...         "CustomObject": ["Account", "Contact"]
            ...     }
            ... )
        """
        version = api_version or self.session.api_version

        # Create package.xml
        package_xml = self._create_retrieve_package(
            component_types, specific_components
        )

        # TODO: Implement SOAP call to retrieve metadata
        # For now, return a stub result
        result = RetrieveResult(
            success=False,
            id="",
            status="NotImplemented",
            messages=["Retrieve not yet implemented - Sprint 2"]
        )

        return result

    def deploy(
        self,
        source_dir: str,
        run_tests: bool = False,
        check_only: bool = False,
        rollback_on_error: bool = True,
    ) -> DeployResult:
        """
        Deploy metadata to Salesforce org.

        Args:
            source_dir: Directory containing metadata to deploy
            run_tests: Whether to run tests during deployment
            check_only: Dry-run mode (validate only, don't deploy)
            rollback_on_error: Rollback all changes if any component fails

        Returns:
            DeployResult with deployment status

        Example:
            >>> # Dry-run deployment
            >>> result = client.metadata.deploy(
            ...     source_dir="./metadata",
            ...     check_only=True
            ... )
            >>>
            >>> # Real deployment with tests
            >>> result = client.metadata.deploy(
            ...     source_dir="./metadata",
            ...     run_tests=True
            ... )
        """
        # TODO: Implement in Sprint 3
        result = DeployResult(
            success=False,
            id="",
            status="NotImplemented",
            messages=["Deploy not yet implemented - Sprint 3"]
        )

        return result

    def deploy_field(
        self,
        field: CustomField,
        check_only: bool = False
    ) -> DeployResult:
        """
        Deploy a single custom field.

        Args:
            field: CustomField to deploy
            check_only: Dry-run mode (validate only)

        Returns:
            DeployResult with deployment status

        Example:
            >>> field = CustomField(
            ...     sobject="Account",
            ...     name="Phone_Verified__c",
            ...     type=FieldType.CHECKBOX,
            ...     label="Phone Verified",
            ...     default_value="false"
            ... )
            >>> result = client.metadata.deploy_field(field)
        """
        # Generate XML
        field_xml = custom_field_to_xml(field)

        # TODO: Implement in Sprint 3
        result = DeployResult(
            success=False,
            id="",
            status="NotImplemented",
            messages=[f"Deploy field {field.name} not yet implemented - Sprint 3"]
        )

        return result

    def deploy_object(
        self,
        obj: CustomObject,
        check_only: bool = False
    ) -> DeployResult:
        """
        Deploy a custom object (with its fields).

        Args:
            obj: CustomObject to deploy
            check_only: Dry-run mode (validate only)

        Returns:
            DeployResult with deployment status

        Example:
            >>> obj = CustomObject(
            ...     name="Product_Review__c",
            ...     label="Product Review",
            ...     plural_label="Product Reviews",
            ...     fields=[
            ...         CustomField(
            ...             sobject="Product_Review__c",
            ...             name="Rating__c",
            ...             type=FieldType.NUMBER,
            ...             label="Rating"
            ...         )
            ...     ]
            ... )
            >>> result = client.metadata.deploy_object(obj)
        """
        # Generate XML
        object_xml = custom_object_to_xml(obj)

        # TODO: Implement in Sprint 3
        result = DeployResult(
            success=False,
            id="",
            status="NotImplemented",
            messages=[f"Deploy object {obj.name} not yet implemented - Sprint 3"]
        )

        return result

    def compare(
        self,
        source_dir: str,
        target_org_session: Optional[SalesforceSession] = None
    ) -> Dict[str, Any]:
        """
        Compare metadata between two orgs or local vs org.

        Args:
            source_dir: Local metadata directory
            target_org_session: Optional session for target org.
                              If None, compares with current org.

        Returns:
            Dictionary with differences

        Example:
            >>> # Compare local metadata with org
            >>> diff = client.metadata.compare(
            ...     source_dir="./metadata"
            ... )
            >>> print(f"New fields: {len(diff['added_fields'])}")
            >>> print(f"Modified: {len(diff['modified'])}")
        """
        # TODO: Implement in Sprint 4
        return {
            "added": [],
            "modified": [],
            "deleted": [],
            "message": "Compare not yet implemented - Sprint 4"
        }

    # Helper methods

    def _create_retrieve_package(
        self,
        component_types: List[str],
        specific_components: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """Create package.xml for retrieve operation."""
        # Use xml_builder to create package.xml
        # For now, simplified version
        return create_package_xml(component_types, self.session.api_version)

    def _create_deploy_zip(self, source_dir: str) -> bytes:
        """Create ZIP file for deployment."""
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            source_path = Path(source_dir)

            for file_path in source_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_path)
                    zip_file.write(file_path, arcname)

        return zip_buffer.getvalue()

    def _extract_retrieve_zip(self, zip_data: bytes, output_dir: str):
        """Extract retrieved metadata ZIP to directory."""
        os.makedirs(output_dir, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
            zip_file.extractall(output_dir)
