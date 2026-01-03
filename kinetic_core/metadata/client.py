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
from kinetic_core.metadata.soap_client import MetadataSOAPClient


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
        self.soap_client = MetadataSOAPClient(session)

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
        return self.soap_client.describe_metadata(api_version)

    def retrieve(
        self,
        component_types: List[str],
        output_dir: str,
        specific_components: Optional[Dict[str, List[str]]] = None,
        api_version: Optional[str] = None,
        wait: bool = True,
        timeout: int = 300,
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
            wait: If True, wait for operation to complete (default: True)
            timeout: Maximum wait time in seconds (default: 300)

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
        # Create package.xml
        package_xml = self._create_retrieve_package(
            component_types, specific_components, api_version
        )

        # Start retrieve operation
        async_id = self.soap_client.retrieve(package_xml, api_version)

        if not wait:
            # Return immediately with async ID
            return RetrieveResult(
                success=False,
                id=async_id,
                status="InProgress",
                messages=[f"Retrieve started. Use check_retrieve_status('{async_id}') to monitor."]
            )

        # Wait for completion
        try:
            status = self.soap_client.wait_for_retrieve(async_id, timeout)
        except TimeoutError as e:
            return RetrieveResult(
                success=False,
                id=async_id,
                status="Timeout",
                messages=[str(e)]
            )

        # Build result
        result = RetrieveResult(
            success=status["success"],
            id=async_id,
            status=status["status"],
            file_properties=status.get("fileProperties", []),
            messages=status.get("messages", []),
            zip_file=status.get("zipFile"),
        )

        # Extract ZIP if successful
        if result.success and result.zip_file:
            self._extract_retrieve_zip(result.zip_file, output_dir)
            result.messages.append(f"Metadata extracted to {output_dir}")

        return result

    def check_retrieve_status(self, async_id: str) -> RetrieveResult:
        """
        Check status of an async retrieve operation.

        Args:
            async_id: Async process ID from retrieve()

        Returns:
            RetrieveResult with current status
        """
        status = self.soap_client.check_retrieve_status(async_id)

        return RetrieveResult(
            success=status["success"],
            id=async_id,
            status=status["status"],
            file_properties=status.get("fileProperties", []),
            messages=status.get("messages", []),
            zip_file=status.get("zipFile"),
        )

    def deploy(
        self,
        source_dir: str,
        run_tests: bool = False,
        check_only: bool = False,
        rollback_on_error: bool = True,
        wait: bool = True,
        timeout: int = 300,
    ) -> DeployResult:
        """
        Deploy metadata to Salesforce org.

        Args:
            source_dir: Directory containing metadata to deploy
            run_tests: Whether to run tests during deployment
            check_only: Dry-run mode (validate only, don't deploy)
            rollback_on_error: Rollback all changes if any component fails
            wait: If True, wait for operation to complete (default: True)
            timeout: Maximum wait time in seconds (default: 300)

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
        # Create ZIP from source directory
        zip_data = self._create_deploy_zip(source_dir)

        # Start deploy operation
        async_id = self.soap_client.deploy(
            zip_data, check_only, run_tests, rollback_on_error
        )

        if not wait:
            # Return immediately
            return DeployResult(
                success=False,
                id=async_id,
                status="InProgress",
                messages=[f"Deploy started. Use check_deploy_status('{async_id}') to monitor."]
            )

        # Wait for completion
        try:
            status = self.soap_client.wait_for_deploy(async_id, timeout)
        except TimeoutError as e:
            return DeployResult(
                success=False,
                id=async_id,
                status="Timeout",
                messages=[str(e)]
            )

        # Build result
        return DeployResult(
            success=status["success"],
            id=async_id,
            status=status["status"],
            component_successes=[s["fullName"] for s in status.get("componentSuccesses", [])],
            component_failures=status.get("componentFailures", []),
            messages=[],
        )

    def check_deploy_status(self, async_id: str) -> DeployResult:
        """
        Check status of an async deploy operation.

        Args:
            async_id: Async process ID from deploy()

        Returns:
            DeployResult with current status
        """
        status = self.soap_client.check_deploy_status(async_id)

        return DeployResult(
            success=status["success"],
            id=async_id,
            status=status["status"],
            component_successes=[s["fullName"] for s in status.get("componentSuccesses", [])],
            component_failures=status.get("componentFailures", []),
            messages=[],
        )

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
        # Create temporary directory with field metadata
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create object directory structure
            obj_dir = Path(tmpdir) / "objects" / field.sobject
            obj_dir.mkdir(parents=True)

            # Write field XML
            field_file = obj_dir / f"{field.name}.field-meta.xml"
            field_xml = custom_field_to_xml(field)
            field_file.write_text(field_xml, encoding="utf-8")

            # Create package.xml
            package_xml = create_package_xml(["CustomField"], self.session.api_version)
            package_file = Path(tmpdir) / "package.xml"
            package_file.write_text(package_xml, encoding="utf-8")

            # Deploy
            return self.deploy(tmpdir, check_only=check_only)

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
        # Create temporary directory with object metadata
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create object directory
            obj_dir = Path(tmpdir) / "objects" / obj.name
            obj_dir.mkdir(parents=True)

            # Write object XML
            obj_file = obj_dir / f"{obj.name}.object-meta.xml"
            obj_xml = custom_object_to_xml(obj)
            obj_file.write_text(obj_xml, encoding="utf-8")

            # Write fields
            for field in obj.fields:
                field_file = obj_dir / f"{field.name}.field-meta.xml"
                field_xml = custom_field_to_xml(field)
                field_file.write_text(field_xml, encoding="utf-8")

            # Create package.xml
            types = ["CustomObject"]
            if obj.fields:
                types.append("CustomField")
            package_xml = create_package_xml(types, self.session.api_version)
            package_file = Path(tmpdir) / "package.xml"
            package_file.write_text(package_xml, encoding="utf-8")

            # Deploy
            return self.deploy(tmpdir, check_only=check_only)

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
        specific_components: Optional[Dict[str, List[str]]] = None,
        api_version: Optional[str] = None,
    ) -> str:
        """Create package.xml for retrieve operation."""
        version = api_version or self.session.api_version

        # Build package.xml manually to support specific members
        from xml.etree import ElementTree as ET

        root = ET.Element("Package")
        root.set("xmlns", "http://soap.sforce.com/2006/04/metadata")

        for comp_type in component_types:
            type_elem = ET.SubElement(root, "types")

            # Add members
            if specific_components and comp_type in specific_components:
                # Specific members
                for member in specific_components[comp_type]:
                    member_elem = ET.SubElement(type_elem, "members")
                    member_elem.text = member
            else:
                # All members
                member_elem = ET.SubElement(type_elem, "members")
                member_elem.text = "*"

            # Add type name
            name_elem = ET.SubElement(type_elem, "name")
            name_elem.text = comp_type

        # Add version
        version_elem = ET.SubElement(root, "version")
        version_elem.text = version

        # Convert to string
        from xml.dom import minidom
        rough_string = ET.tostring(root, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="    ", encoding=None)

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
