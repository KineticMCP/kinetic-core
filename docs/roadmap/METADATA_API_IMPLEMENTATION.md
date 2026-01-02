# Metadata API Implementation Roadmap

**Project:** kinetic-core Metadata API Support
**Target Version:** v2.1.0
**Status:** Planning
**Last Updated:** 2025-01-02

---

## 🎯 Executive Summary

### Obiettivo

Implementare **Salesforce Metadata API** in kinetic-core per permettere la gestione programmatica della configurazione Salesforce (campi custom, oggetti, validation rules, workflow, ecc.).

### Perché è Importante

**Problema attuale:**
- ❌ Configurazione Salesforce solo via Web UI (lento, manuale, error-prone)
- ❌ Nessun versionamento delle configurazioni
- ❌ Deployment tra ambienti difficile e manuale
- ❌ Setup clienti richiede ore di click

**Soluzione con Metadata API:**
- ✅ Configurazione programmatica via codice
- ✅ Versionamento con Git (Configuration as Code)
- ✅ Deployment automatizzato tra ambienti
- ✅ Setup clienti in minuti invece di ore
- ✅ Rollback facile a configurazioni precedenti

### Benefici Attesi

| Aspetto | Prima | Dopo | Miglioramento |
|---------|-------|------|---------------|
| **Setup nuovo cliente** | 2-3 ore | 5 minuti | 24-36x più veloce |
| **Deployment Sandbox→Prod** | 1-2 ore | 10 minuti | 6-12x più veloce |
| **Errori configurazione** | Frequenti | Rari | Validazione automatica |
| **Documentazione** | Assente | Automatica | XML versionato |
| **Rollback** | Difficile | Immediato | Git revert |

---

## 📊 Scope & Features

### FASE 1: Metadata Retrieval (Read-Only) ⭐ PRIORITÀ ALTA

Implementare capacità di **leggere** metadata esistenti.

#### Features

**1.1 Retrieve Metadata Components**
```python
client.metadata.retrieve(
    component_types=["CustomObject", "CustomField"],
    package_names=["*__c"],  # Tutti custom objects
    output_dir="./metadata_backup"
)
```

**Componenti supportati (Fase 1):**
- ✅ Custom Objects (`CustomObject`)
- ✅ Custom Fields (`CustomField`)
- ✅ Validation Rules (`ValidationRule`)
- ✅ Workflow Rules (`WorkflowRule`)
- ✅ Page Layouts (`Layout`)
- ✅ Record Types (`RecordType`)
- ✅ Profiles (`Profile`)
- ✅ Permission Sets (`PermissionSet`)

**Output:**
- File XML per ogni componente
- `package.xml` con manifest
- Struttura compatibile con SFDX/Salesforce CLI

**Casi d'Uso:**
1. **Backup automatico** configurazione org
2. **Documentazione** automatica
3. **Analisi differenze** tra org
4. **Versionamento** con Git

---

### FASE 2: Metadata Deployment (Write) ⭐ PRIORITÀ ALTA

Implementare capacità di **creare/modificare** metadata.

#### Features

**2.1 Deploy Metadata Package**
```python
result = client.metadata.deploy(
    source_dir="./metadata_to_deploy",
    run_tests=True,
    rollback_on_error=True,
    check_only=False  # False = deploy reale, True = dry-run
)
```

**2.2 Create Custom Field**
```python
field = CustomField(
    sobject="Account",
    name="Phone_Verified__c",
    label="Phone Verified",
    type="Checkbox",
    default_value=False,
    description="Indicates if phone has been verified"
)

result = client.metadata.deploy_field(field)
```

**2.3 Create Custom Object**
```python
obj = CustomObject(
    name="Customer_Feedback__c",
    label="Customer Feedback",
    plural_label="Customer Feedbacks",
    fields=[
        CustomField(name="Rating__c", type="Number", ...),
        CustomField(name="Comment__c", type="TextArea", ...),
        CustomField(name="Customer__c", type="Lookup", ...)
    ]
)

result = client.metadata.deploy_object(obj)
```

**2.4 Validation & Safety**
- ✅ XML schema validation
- ✅ Dry-run mode (preview changes)
- ✅ Dependency checking
- ✅ Rollback automatico su errore
- ✅ Test execution obbligatoria per Production

**Casi d'Uso:**
1. **Provisioning clienti** automatizzato
2. **Deployment CI/CD** Sandbox → Production
3. **Setup ambienti** identici (Training, Demo)
4. **Migrazione** configurazioni tra org

---

### FASE 3: Advanced Metadata Operations ⭐ PRIORITÀ MEDIA

Features avanzate per gestione metadata.

#### Features

**3.1 Metadata Comparison**
```python
diff = client.metadata.compare(
    source_org=sandbox_client,
    target_org=production_client,
    component_types=["CustomObject", "CustomField"]
)

# Output
{
    "missing_in_target": [...],
    "different_values": [...],
    "extra_in_target": [...]
}
```

**3.2 Selective Deployment**
```python
# Deploy solo componenti modificati
changed = client.metadata.get_changed_components(
    since_date="2025-01-01"
)

client.metadata.deploy(
    components=changed,
    target_org=production_client
)
```

**3.3 Metadata Templates**
```python
# Template per setup standard
template = MetadataTemplate("enterprise_crm")

template.apply(client, params={
    "company_name": "Acme Corp",
    "industry": "Technology"
})

# Crea automaticamente:
# - Custom objects standard
# - Fields configurati
# - Workflows
# - Validation rules
```

**3.4 Conflict Resolution**
```python
result = client.metadata.deploy(
    source_dir="./metadata",
    on_conflict="prompt"  # ask, overwrite, skip, merge
)
```

---

### FASE 4: Code Components Deployment ⭐ PRIORITÀ BASSA

Deploy di componenti codice.

#### Features

**4.1 Apex Classes & Triggers**
```python
apex_class = ApexClass(
    name="AccountTriggerHandler",
    body="""
    public class AccountTriggerHandler {
        public static void beforeInsert(List<Account> accounts) {
            // Logic here
        }
    }
    """
)

client.metadata.deploy_apex(apex_class, run_tests=True)
```

**4.2 Lightning Components**
```python
lwc = LightningWebComponent(
    name="customerFeedback",
    markup="<template>...</template>",
    javascript="import { LightningElement } from 'lwc';...",
    css=".container { ... }"
)

client.metadata.deploy_lwc(lwc)
```

**Note:** Fase 4 opzionale, priorità bassa rispetto a configurazioni.

---

## 🏗️ Architettura Proposta

### Struttura Moduli

```
kinetic_core/
├── metadata/                   # ⭐ NUOVO MODULO
│   ├── __init__.py
│   ├── client.py              # MetadataClient
│   ├── models.py              # CustomObject, CustomField, etc.
│   ├── xml_builder.py         # Genera XML Salesforce
│   ├── xml_parser.py          # Parse XML responses
│   ├── deployer.py            # Deploy operations
│   ├── retriever.py           # Retrieve operations
│   ├── validator.py           # Validazione componenti
│   ├── comparator.py          # Confronto metadata
│   └── templates/             # Template predefiniti
│       ├── enterprise_crm.py
│       ├── sales_pipeline.py
│       └── customer_support.py
```

### API Design

```python
# kinetic_core/core/client.py (modificato)

class SalesforceClient:
    def __init__(self, session):
        self.session = session
        self._bulk_client = None
        self._metadata_client = None  # ⭐ NUOVO

    @property
    def metadata(self):
        """Access Metadata API operations."""
        if not self._metadata_client:
            from kinetic_core.metadata import MetadataClient
            self._metadata_client = MetadataClient(self.session)
        return self._metadata_client
```

### MetadataClient API

```python
# kinetic_core/metadata/client.py

class MetadataClient:
    """Salesforce Metadata API client."""

    def __init__(self, session: SalesforceSession):
        self.session = session
        self.base_url = f"{session.instance_url}/services/Soap/m/{session.api_version}"

    # RETRIEVE Operations
    def retrieve(
        self,
        component_types: List[str],
        package_names: Optional[List[str]] = None,
        output_dir: str = "./metadata"
    ) -> RetrieveResult:
        """Retrieve metadata components from org."""
        pass

    def describe_metadata(self) -> MetadataDescription:
        """Get list of all metadata types available."""
        pass

    # DEPLOY Operations
    def deploy(
        self,
        source_dir: str,
        run_tests: bool = False,
        rollback_on_error: bool = True,
        check_only: bool = False
    ) -> DeployResult:
        """Deploy metadata package to org."""
        pass

    def deploy_field(
        self,
        field: CustomField,
        check_only: bool = False
    ) -> DeployResult:
        """Deploy single custom field."""
        pass

    def deploy_object(
        self,
        obj: CustomObject,
        check_only: bool = False
    ) -> DeployResult:
        """Deploy custom object with fields."""
        pass

    # COMPARISON Operations
    def compare(
        self,
        source_org: 'SalesforceClient',
        target_org: 'SalesforceClient',
        component_types: List[str]
    ) -> MetadataDiff:
        """Compare metadata between two orgs."""
        pass

    # UTILITY Operations
    def validate_package(self, source_dir: str) -> ValidationResult:
        """Validate metadata package before deployment."""
        pass

    def get_deployment_status(self, async_process_id: str) -> DeployResult:
        """Check status of async deployment."""
        pass
```

---

## 📋 Data Models

### CustomField Model

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class CustomField:
    """Represents a Salesforce custom field."""

    sobject: str                    # Parent object
    name: str                       # API name (e.g., "Phone_Verified__c")
    label: str                      # Display label
    type: str                       # Checkbox, Text, Number, etc.

    # Optional attributes
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    default_value: Optional[Any] = None
    description: Optional[str] = None
    help_text: Optional[str] = None
    required: bool = False
    unique: bool = False
    external_id: bool = False

    # For formula fields
    formula: Optional[str] = None

    # For lookup/master-detail
    reference_to: Optional[str] = None
    relationship_name: Optional[str] = None

    # Picklist values
    picklist_values: Optional[List[str]] = None

    def to_xml(self) -> str:
        """Convert to Salesforce metadata XML."""
        pass

    @classmethod
    def from_xml(cls, xml: str) -> 'CustomField':
        """Parse from Salesforce metadata XML."""
        pass
```

### CustomObject Model

```python
@dataclass
class CustomObject:
    """Represents a Salesforce custom object."""

    name: str                       # API name (e.g., "Customer_Feedback__c")
    label: str                      # Display label
    plural_label: str               # Plural label

    # Object properties
    description: Optional[str] = None
    deployment_status: str = "Deployed"  # Deployed or InDevelopment
    sharing_model: str = "ReadWrite"     # Private, Read, ReadWrite

    # Features
    enable_activities: bool = False
    enable_reports: bool = True
    enable_search: bool = True
    enable_bulk_api: bool = True
    enable_sharing: bool = True
    enable_streaming_api: bool = True

    # Fields
    fields: List[CustomField] = field(default_factory=list)

    # Name field configuration
    name_field_label: str = "Name"
    name_field_type: str = "Text"  # Text or AutoNumber

    def to_xml(self) -> str:
        """Convert to Salesforce metadata XML."""
        pass

    @classmethod
    def from_xml(cls, xml: str) -> 'CustomObject':
        """Parse from Salesforce metadata XML."""
        pass
```

### Deploy/Retrieve Results

```python
@dataclass
class DeployResult:
    """Result of metadata deployment."""

    id: str                         # Async process ID
    status: str                     # Succeeded, Failed, InProgress
    success: bool
    done: bool

    # Component details
    components_deployed: int = 0
    components_total: int = 0

    # Test results (if run_tests=True)
    tests_run: int = 0
    tests_failed: int = 0

    # Errors
    errors: List[Dict[str, Any]] = field(default_factory=list)

    # Deployment details
    created_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

    @property
    def is_complete(self) -> bool:
        return self.done

    @property
    def is_successful(self) -> bool:
        return self.success and self.done


@dataclass
class RetrieveResult:
    """Result of metadata retrieval."""

    id: str
    status: str
    success: bool
    done: bool

    # Retrieved files
    zip_file: Optional[bytes] = None
    file_count: int = 0

    # Errors
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def extract_to(self, directory: str) -> None:
        """Extract ZIP to directory."""
        pass
```

---

## 🔄 Integration Flow

### Example 1: Retrieve & Version Control

```python
from kinetic_core import JWTAuthenticator, SalesforceClient

# Authenticate
auth = JWTAuthenticator.from_env()
session = auth.authenticate()
client = SalesforceClient(session)

# Retrieve all custom metadata
result = client.metadata.retrieve(
    component_types=["CustomObject", "CustomField", "ValidationRule"],
    package_names=["*__c"],  # All custom components
    output_dir="./salesforce_metadata"
)

# Result structure:
# ./salesforce_metadata/
# ├── package.xml
# ├── objects/
# │   ├── Account.object
# │   ├── Customer_Feedback__c.object
# │   └── ...
# ├── fields/
# │   ├── Account/Phone_Verified__c.field
# │   └── ...
# └── validationRules/
#     └── ...

# Commit to Git
import subprocess
subprocess.run(["git", "add", "salesforce_metadata/"])
subprocess.run(["git", "commit", "-m", "Backup Salesforce config"])
subprocess.run(["git", "push"])
```

---

### Example 2: Create Custom Field

```python
from kinetic_core.metadata import CustomField

# Define field
field = CustomField(
    sobject="Account",
    name="Phone_Verified__c",
    label="Phone Verified",
    type="Checkbox",
    default_value=False,
    description="Indicates if phone number has been verified by customer",
    help_text="Check this box when customer confirms their phone number"
)

# Deploy (dry-run first)
dry_run_result = client.metadata.deploy_field(field, check_only=True)

if dry_run_result.success:
    print("✓ Validation passed")

    # Deploy for real
    result = client.metadata.deploy_field(field)

    if result.is_successful:
        print(f"✓ Field created: {field.name}")
    else:
        print(f"✗ Errors: {result.errors}")
```

---

### Example 3: Deploy Package Sandbox → Production

```python
# Step 1: Retrieve from Sandbox
sandbox_auth = JWTAuthenticator(
    client_id=SANDBOX_CLIENT_ID,
    username=SANDBOX_USERNAME,
    private_key_path=SANDBOX_KEY_PATH,
    login_url="https://test.salesforce.com"
)
sandbox_session = sandbox_auth.authenticate()
sandbox_client = SalesforceClient(sandbox_session)

sandbox_client.metadata.retrieve(
    component_types=["CustomObject", "CustomField"],
    output_dir="./sandbox_metadata"
)

# Step 2: Deploy to Production
prod_auth = JWTAuthenticator(
    client_id=PROD_CLIENT_ID,
    username=PROD_USERNAME,
    private_key_path=PROD_KEY_PATH,
    login_url="https://login.salesforce.com"
)
prod_session = prod_auth.authenticate()
prod_client = SalesforceClient(prod_session)

# Dry-run first
dry_run = prod_client.metadata.deploy(
    source_dir="./sandbox_metadata",
    run_tests=True,
    check_only=True
)

if dry_run.success:
    print(f"✓ Validation passed, {dry_run.tests_run} tests run")

    # Deploy for real
    result = prod_client.metadata.deploy(
        source_dir="./sandbox_metadata",
        run_tests=True,
        rollback_on_error=True
    )

    if result.is_successful:
        print("✓ Deployment successful")
    else:
        print(f"✗ Deployment failed: {result.errors}")
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_metadata_client.py

def test_custom_field_to_xml():
    field = CustomField(
        sobject="Account",
        name="Test__c",
        label="Test Field",
        type="Text",
        length=255
    )

    xml = field.to_xml()
    assert "<fullName>Test__c</fullName>" in xml
    assert "<label>Test Field</label>" in xml
    assert "<type>Text</type>" in xml
    assert "<length>255</length>" in xml


def test_custom_field_from_xml():
    xml = """
    <CustomField>
        <fullName>Test__c</fullName>
        <label>Test Field</label>
        <type>Text</type>
        <length>255</length>
    </CustomField>
    """

    field = CustomField.from_xml(xml)
    assert field.name == "Test__c"
    assert field.label == "Test Field"
    assert field.type == "Text"
    assert field.length == 255
```

### Integration Tests

```python
# tests/test_metadata_integration.py

@pytest.mark.integration
def test_deploy_custom_field():
    client = create_test_client()

    field = CustomField(
        sobject="Account",
        name=f"Test_{uuid.uuid4().hex[:8]}__c",
        label="Integration Test Field",
        type="Text",
        length=100
    )

    # Deploy
    result = client.metadata.deploy_field(field)
    assert result.is_successful

    # Verify field exists
    metadata = client.describe("Account")
    field_names = [f['name'] for f in metadata['fields']]
    assert field.name in field_names

    # Cleanup
    # TODO: Delete field (future feature)


@pytest.mark.integration
def test_retrieve_metadata():
    client = create_test_client()

    result = client.metadata.retrieve(
        component_types=["CustomObject"],
        package_names=["Account"],
        output_dir=f"./test_metadata_{uuid.uuid4().hex[:8]}"
    )

    assert result.is_successful
    assert result.file_count > 0

    # Cleanup temp directory
```

---

## 📦 Dependencies

### New Dependencies

```python
# requirements.txt additions

# XML processing
lxml>=4.9.0              # XML parsing & generation
xmltodict>=0.13.0        # XML to dict conversion

# ZIP handling
zipfile36>=0.1.3         # Enhanced ZIP support

# Testing
pytest-mock>=3.12.0      # Mocking for tests
```

### Salesforce API Versions

- **Metadata API**: v60.0+
- **SOAP API**: Required for Metadata operations
- **REST API**: Used for describe operations

---

## 📅 Implementation Timeline

### Sprint 1 (Week 1-2): Foundation ⭐ FASE 1

**Goals:**
- ✅ Setup metadata module structure
- ✅ Implement data models (CustomField, CustomObject)
- ✅ XML serialization/deserialization
- ✅ Basic retrieve functionality

**Deliverables:**
- `metadata/` module with structure
- `CustomField` and `CustomObject` models
- `xml_builder.py` and `xml_parser.py`
- `retriever.py` basic implementation
- Unit tests for models

**Time Estimate:** 15-20 hours

---

### Sprint 2 (Week 3): Retrieve Operations ⭐ FASE 1

**Goals:**
- ✅ Complete retrieve implementation
- ✅ Package.xml generation
- ✅ ZIP extraction
- ✅ Integration tests

**Deliverables:**
- Full `MetadataClient.retrieve()` working
- Support for all Fase 1 component types
- Integration tests with real Salesforce org
- Documentation

**Time Estimate:** 10-15 hours

---

### Sprint 3 (Week 4-5): Deploy Operations ⭐ FASE 2

**Goals:**
- ✅ Implement deploy functionality
- ✅ Validation logic
- ✅ Dry-run mode
- ✅ Rollback mechanism

**Deliverables:**
- `deployer.py` complete
- `validator.py` with XML validation
- Deploy single field/object helpers
- Error handling and reporting

**Time Estimate:** 20-25 hours

---

### Sprint 4 (Week 6): Advanced Features ⭐ FASE 3

**Goals:**
- ✅ Metadata comparison
- ✅ Selective deployment
- ✅ Templates system

**Deliverables:**
- `comparator.py` with diff logic
- Template examples (enterprise_crm, etc.)
- CLI tool for metadata operations
- Performance optimizations

**Time Estimate:** 15-20 hours

---

**Total Time Estimate:** 60-80 hours (1.5-2 mesi part-time)

---

## 🎯 Success Criteria

### Fase 1 Complete When:
- ✅ Can retrieve all custom objects from org
- ✅ Can retrieve all custom fields
- ✅ Output is valid Salesforce package format
- ✅ Can extract to directory with correct structure
- ✅ Integration tests pass

### Fase 2 Complete When:
- ✅ Can deploy custom field to org
- ✅ Can deploy custom object with fields
- ✅ Validation prevents invalid deployments
- ✅ Dry-run mode works correctly
- ✅ Rollback works on error
- ✅ Can deploy between Sandbox and Production

### Fase 3 Complete When:
- ✅ Can compare two orgs
- ✅ Can deploy only changed components
- ✅ Templates work for common scenarios
- ✅ Performance is acceptable (< 5 min for 100 components)

---

## 🚨 Risks & Mitigations

### Risk 1: Salesforce API Complexity

**Risk:** Metadata API è complessa, XML verbose, molte edge cases

**Mitigation:**
- Start with simple components (CustomField)
- Incremental implementation
- Extensive testing with real org
- Follow Salesforce best practices

---

### Risk 2: Breaking Changes

**Risk:** Modifiche metadata possono rompere org production

**Mitigation:**
- ✅ Dry-run mode ALWAYS default
- ✅ Rollback automatico su errore
- ✅ Test execution obbligatoria per Production
- ✅ Backup automatico prima di deploy
- ✅ Validazione rigorosa input

---

### Risk 3: Performance

**Risk:** Retrieve/deploy di 1000+ componenti può essere lento

**Mitigation:**
- Async operations con polling
- Parallel processing dove possibile
- Caching metadata descrittivi
- Progress callbacks per feedback utente

---

### Risk 4: XML Schema Changes

**Risk:** Salesforce può cambiare schema XML tra versioni

**Mitigation:**
- Use Salesforce metadata describe API
- Version-agnostic parsing where possible
- Test against multiple API versions
- Clear error messages for unsupported features

---

## 🔄 KineticMCP Integration

### New MCP Tools

Quando Metadata API sarà in kinetic-core, aggiungeremo questi tools in KineticMCP:

```python
# kineticmcp/src/mcp_salesforce_server/server.py

@mcp.tool()
def sf_create_field(
    ctx: Context,
    sobject: str,
    field_name: str,
    field_type: str,
    label: str,
    **options
) -> Dict[str, Any]:
    """Create custom field on Salesforce object."""
    client = get_client_for_session(ctx)

    field = CustomField(
        sobject=sobject,
        name=field_name,
        label=label,
        type=field_type,
        **options
    )

    result = client.metadata.deploy_field(field)
    return result.to_dict()


@mcp.tool()
def sf_backup_metadata(
    ctx: Context,
    component_types: List[str],
    output_dir: str = "./salesforce_backup"
) -> Dict[str, Any]:
    """Backup Salesforce metadata to local directory."""
    client = get_client_for_session(ctx)

    result = client.metadata.retrieve(
        component_types=component_types,
        output_dir=output_dir
    )

    return {
        "success": result.success,
        "file_count": result.file_count,
        "output_dir": output_dir
    }


@mcp.tool()
def sf_deploy_metadata(
    ctx: Context,
    source_dir: str,
    run_tests: bool = True,
    check_only: bool = False
) -> Dict[str, Any]:
    """Deploy metadata package to Salesforce."""
    client = get_client_for_session(ctx)

    result = client.metadata.deploy(
        source_dir=source_dir,
        run_tests=run_tests,
        check_only=check_only,
        rollback_on_error=True
    )

    return {
        "success": result.success,
        "components_deployed": result.components_deployed,
        "tests_run": result.tests_run,
        "tests_failed": result.tests_failed,
        "errors": result.errors
    }
```

---

## 📚 Documentation Plan

### kinetic-core Docs

Create:
- `docs/api/METADATA_API.md` - Complete API reference
- `docs/guides/METADATA_QUICKSTART.md` - Quick start guide
- `docs/examples/METADATA_EXAMPLES.md` - Practical examples

Update:
- `README.md` - Add Metadata API section
- `CHANGELOG.md` - Document v2.1.0 changes

### KineticMCP Docs

Update when integrated:
- `docs/TOOLS_REFERENCE.md` - Add new metadata tools
- `docs/METADATA_GUIDE.md` - User guide for metadata operations
- `CHANGELOG.md` - New version with metadata support

---

## 🎓 References

- [Salesforce Metadata API Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/)
- [Metadata Types Reference](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_types_list.htm)
- [SFDX Project Structure](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_source_file_format.htm)

---

## ✅ Next Steps

1. **Review & Approval**: Review questa roadmap
2. **Prioritization**: Confermare priorità Fase 1-2
3. **Environment Setup**: Configurare Salesforce org per testing
4. **Sprint Kickoff**: Iniziare Sprint 1

---

**Roadmap Prepared By:** Claude Code
**For Project:** kinetic-core v2.1.0
**Date:** 2025-01-02

**Status:** 📋 Ready for Review
