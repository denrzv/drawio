# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python utility for processing C4 architecture diagrams created in draw.io. It validates diagram elements against C4 model conventions and exports to Excel (XLSX) and Structurizr DSL formats.

## Installation

No external dependencies. Requires Python 3 standard library only.

## Running the Parser

```bash
python3 drawio_parser.py -i <inputfile.drawio> [-i <inputfile.drawio> ...] [-d] [-s] [-H]
```

- `-i` — input draw.io file (required; supports both compressed and uncompressed XML formats). Can be repeated to merge several diagrams into one model.
- `-d` — enable data syntax validation for relation descriptions
- `-s` — print statistics (component/relation counts)
- `-H`/`--hierarchical` — write hierarchical DSL output: `workspace.dsl` plus `relationships/*.dsl` and `views/*.dsl` files included from the workspace.

DSL output is always written to `workspace.dsl` in the current directory.

## Code Architecture

### Entry point: `drawio_parser.py`

**Parsing pipeline** (executed in `main()`):
1. `load_from_xml()` — reads the draw.io file, handling both compressed (base64+zlib) and plain XML. Populates three collections: `components` (dict by id), `relations` (list), `broken_relations` (list).
2. `fill_parent_id()` — establishes parent-child hierarchy by checking geometric containment (bounding-box intersection).
3. `fix_broken_relations()` — attempts to repair arrows that aren't connected to a component by matching their endpoint coordinates against component bounding boxes, picking the smallest enclosing component.
4. `fix_missing_relations()` — drops any relation whose source or target no longer exists in the component dict.
5. Validation: `check_relations()` and `check_components()` print numbered issues to stdout.
6. Export: `export_to_dsl()` or, with `-H`, `export_to_hierarchical_dsl()`.

### Data model

- **`Object`** — base class; reads all `c4*` attributes and the `cmdb` attribute dynamically from the draw.io XML element's attribute dict.
- **`Element(Object)`** — a C4 component; adds `left_top`, `right_bottom` (coordinates) and `parent_id`.
- **`Relation(Object)`** — a fully connected arrow; adds `source` and `target` (component ids).
- **`BrokenRelation(Object)`** — an arrow missing source or target; also stores `source_point`/`target_point` coordinates used during the repair pass.

### C4 attribute conventions

draw.io element attributes that matter:
- `c4Type` — determines node kind: `Relationship`, `Person`, `Software System`, `Container`, `Component`, `SystemScopeBoundary`, `ContainerScopeBoundary`.
- `c4Name` — display name.
- `c4Description` — description; for relations must follow the notation `action (input data): output data [technology]`.
- `c4Technology` — technology stack label.
- `cmdb` — optional CMDB identifier, written as a Structurizr `properties` block.

### DSL export (`export_to_dsl`)

Walks the component hierarchy recursively (`recurse_walk`), emitting Structurizr DSL at depth 1 (softwareSystem/Person), 2 (container), 3 (component). Variable names are generated from the Russian/Latin `c4Name` via a transliteration table (`symbols` list); duplicates get a numeric suffix. Always outputs `workspace.dsl`.

### Hierarchical DSL export (`export_to_hierarchical_dsl`)

When `-H`/`--hierarchical` is set, the parser can merge repeated `-i` diagrams by component type/name, treating `SystemScopeBoundary` as the same logical software system as a `Software System` with the same name. It writes top-level systems and containers into `workspace.dsl`, system-level relationships into `relationships/system-context.dsl`, container/component relationships into `relationships/container-<system>.dsl`, and view definitions into `views/*.dsl`.

### `drawio_print.py`

Standalone diagnostic script that reads uncompressed draw.io XML and prints raw `mxCell` values. Useful for inspecting raw diagram structure.

## Validation Rules

`check_components()` flags:
- Missing `c4Description` (except `SystemScopeBoundary`, `ContainerScopeBoundary`, `Person`).
- Missing `c4Technology` (except `Software System`, `Person`, boundaries).
- Components with no inbound or outbound relations (walks up to parent if needed).

`check_relations()` flags:
- Missing `c4Technology` (skipped when source or target is a `Person`).
- With `-d`: missing input-data pattern `(...)` or output-data pattern `):...` in `c4Description`.

## File I/O Conventions

- Input: `.drawio` files (gitignored).
- DSL output: `workspace.dsl` (gitignored).
- Diagram and output files are excluded from git; only source code is tracked.
