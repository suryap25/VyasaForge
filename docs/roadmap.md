# VyasaForge Roadmap

## Phase 1 Complete

The current MVP can generate and compile structured document chapters through a
controlled pipeline:

- TOC planning
- chapter brief generation
- chapter writing
- validation
- repair
- review
- revision
- finalization
- QA
- DOCX/PDF compilation through Pandoc
- provider abstraction through LiteLLM
- token usage logging
- chapter state tracking
- per-handbook workspaces

## Phase 2 In Progress

Reliability and scale work is ongoing:

- stronger structured reviewer output
- more reliable revision patching
- richer deterministic QA
- multi-chapter compile and dashboard improvements
- better reference quality gates
- improved failure recovery
- broader provider testing

## Future Roadmap

### Generic Document Production Engine

- Make non-AppSec handbook templates first-class.
- Allow reusable handbook archetypes.
- Support topic-specific required sections and quality gates.

### Better Planning

- Improve TOC planner validation.
- Add explicit no-guess clarification loops.
- Add topic/audience/depth presets.

### Quality Layer

- Add semantic duplicate detection across chapters.
- Add terminology consistency checks.
- Add glossary and appendix generation.
- Add citation/reference validation.

### Compiler v2

- Improve DOCX styling.
- Add cover templates.
- Add glossary and appendix sections.
- Improve PDF support.

### Developer Experience

- Add automated tests.
- Add linting and typing gates.
- Add release automation.
- Add example handbook fixtures without committing generated private content.

## Out of Scope

The sketchnote and diagram generation layers were removed. The current roadmap
focuses on reliable text generation, validation, and document compilation.
