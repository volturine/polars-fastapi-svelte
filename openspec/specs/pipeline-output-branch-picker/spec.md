## ADDED Requirements

### Requirement: Output branch picker supports create prompt
The system MUST allow users to create a new branch from the output datasource branch picker when the control is configured to allow creation.

#### Scenario: Create prompt appears for output datasource
- **WHEN** the output datasource branch picker is rendered with create enabled
- **THEN** the picker shows a create-new-branch prompt when the user types a branch name that does not exist

#### Scenario: Create prompt is hidden when disabled
- **WHEN** the output datasource branch picker is rendered with create disabled
- **THEN** the picker does not offer a create-new-branch option
