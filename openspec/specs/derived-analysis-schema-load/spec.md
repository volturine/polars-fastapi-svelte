## ADDED Requirements

### Requirement: Derived analysis tabs load schema on creation
The system MUST load schema for derived analysis tabs so new nodes receive column metadata immediately after tab creation.

#### Scenario: Derived tab creation hydrates schema
- **WHEN** a derived analysis tab is created from an existing analysis output
- **THEN** the schema is loaded for that tab's datasource before the user configures steps

#### Scenario: New node uses loaded schema
- **WHEN** a user adds a node to a derived analysis tab
- **THEN** the node configuration UI receives populated schema columns
