## Context

Recent frontend changes to pipeline tab schema alignment appear to have broken two UI behaviors: the output datasource branch picker no longer offers a create-new-branch prompt, and derived analysis tabs fail to load schema, leaving new nodes without populated column metadata. These issues affect the pipeline editing flow in `OutputNode`, `BranchPicker`, analysis tab creation, and schema store hydration.

## Goals / Non-Goals

**Goals:**
- Restore branch creation in the output datasource branch picker without regressing existing selection behavior.
- Ensure derived analysis tabs trigger schema loading and populate nodes so step configuration can resolve columns.
- Add regression coverage for both behaviors.

**Non-Goals:**
- Redesign the branch picker UI or datasource schema model.
- Change backend compute or datasource APIs unless required to fix frontend hydration.

## Decisions

- **Reuse BranchPicker create flow**: Re-enable/restore the create option in the existing BranchPicker component, keeping its API and behavior consistent with prior usage. This minimizes UI changes and limits the fix to the regression.
  - *Alternative:* Replace BranchPicker with a new control or custom modal. Rejected due to scope and higher regression risk.

- **Normalize derived tab schema load in store**: Ensure that analysis tab creation and derived analysis tabs call schema loading routines (or schema store hydration) after tab creation and output datasource assignment. This centralizes behavior in stores/utilities rather than scattering in UI components.
  - *Alternative:* Manually load schema only in the derived tab UI. Rejected because it duplicates logic and risks missing other flows.

- **Regression checks at store/pipeline level**: Add checks/tests that verify derived tabs receive schema and that branch picker exposes create prompts for output datasources. Focus on store utilities or UI integration where currently tested.
  - *Alternative:* No tests, rely on manual QA. Rejected due to repeated regressions.

## Risks / Trade-offs

- **Risk:** Branch picker create option might appear for datasources where it should not be allowed. 
  → **Mitigation:** Preserve existing gating logic (e.g., allowCreate flag) and only restore previous behavior for output nodes.

- **Risk:** Schema loading could introduce extra fetches on tab creation. 
  → **Mitigation:** Load schema only when missing and reuse existing cache/store checks.

- **Risk:** Derived tab schema load depends on output datasource ID availability. 
  → **Mitigation:** Ensure output configuration is created before schema load and guard with early returns if IDs are missing.
