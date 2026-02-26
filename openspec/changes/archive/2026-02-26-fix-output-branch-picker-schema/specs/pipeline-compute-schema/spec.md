## MODIFIED Requirements

### Requirement: Tab output configuration is required
Each analysis pipeline tab MUST include an `output` object with `output_datasource_id`, `datasource_type`, `format`, and `filename` fields. The system MUST hydrate schema for tabs created from an analysis output before node configuration begins.

#### Scenario: Missing output object
- **WHEN** a tab is submitted without an `output` object
- **THEN** the request fails with a validation error stating output configuration is required

#### Scenario: Missing output datasource id
- **WHEN** a tab is submitted with `output` but without `output.output_datasource_id`
- **THEN** the request fails with a validation error stating `output.output_datasource_id` is required

#### Scenario: Derived tab schema hydration
- **WHEN** a tab is created from an upstream analysis output
- **THEN** the schema is loaded for the tab's datasource before node configuration is available
