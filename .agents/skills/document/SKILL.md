---
name: document
description: Structured workflow for writing or revising documentation, proposals, technical specs, decision docs, RFCs, PRDs, runbooks, and similar long-form docs. Use when the user wants to draft a document, improve an existing doc, create a template-based writeup, or pressure-test whether a document will make sense to readers with less context.
---

# Document

Guide the user through three stages:

1. Context gathering
2. Section-by-section drafting and refinement
3. Reader testing

Keep the workflow procedural. Adapt it to the user's pace rather than forcing every sub-step.

## Runtime Inputs

- Working directory for local drafts
- Document type, if known
- Audience and desired outcome
- Optional existing draft or template file

## Automation

- Scaffold a local draft: `python3 <skill-dir>/scripts/scaffold_doc.py <output-path> <doc-type> [title]`
- Generate reader-test questions from a draft: `python3 <skill-dir>/scripts/reader_questions.py <doc-path> [count]`

Read these references when needed:

- `references/doc_types.md`: default section structures by doc type
- `references/refinement.md`: how to drive section drafting and editing
- `references/reader_testing.md`: how to pressure-test a doc with a fresh reader

## Workflow

### Stage 1: Context Gathering

Goal: close the gap between what the user knows and what the draft currently explains.

Ask for:

1. Doc type
2. Audience
3. Desired decision, action, or understanding
4. Constraints or required format
5. Existing sources, drafts, or templates

Encourage an unstructured info dump after the initial questions. Ask clarifying questions only after enough raw context exists to ask good ones.

If the user has an existing draft or template:

- read it first
- identify missing context, weak structure, and assumptions the draft makes about the reader

If the user only has notes:

- summarize the notes back as a draftable outline before writing sections

### Stage 2: Drafting and Refinement

Goal: build the document section by section, starting with the highest-uncertainty section.

For each section:

1. Ask focused clarifying questions
2. Brainstorm what belongs in the section
3. Ask the user what to keep, remove, or combine
4. Draft the section in the file
5. Refine with small edits until the section is stable

Prefer writing into a local markdown file in the workspace so the user and assistant can iterate on the same draft.

Use `scaffold_doc.py` when the structure is unclear or the user wants a fast starting point.

During refinement:

- prefer surgical edits over full rewrites
- remove filler and duplicated rationale
- ask whether anything can be deleted without losing meaning
- keep summaries and introductions until late, after the hard sections are stable

### Stage 3: Reader Testing

Goal: verify that a reader with less context can still answer the important questions from the document.

Use `reader_questions.py` to generate concrete reader questions from the current draft.

Then test the draft by asking:

1. Can a fresh reader answer the key questions correctly?
2. What assumptions does the document make without stating them?
3. Where is the document ambiguous, internally inconsistent, or overly compressed?

If direct reader testing is not possible, simulate it by reading the draft as if you did not have the session context and list the likely failure points explicitly.

Loop back to refinement for any weak sections.

## Rules

- Keep the workflow generic and local-first; do not assume any product-specific artifact, connector, or sub-agent environment.
- Use local files and whatever file-editing tools are available in the current environment.
- Ask before pulling in large external context sources the user has only mentioned vaguely.
- Prefer concise, high-signal prose over exhaustive coverage.
- The document is not done until reader-testing questions are answerable from the draft itself.

## Output

Report:

1. Current document state
2. What changed in this pass
3. Remaining gaps before the doc is ready
