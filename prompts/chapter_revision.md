# Chapter Revision Prompt

You are revising an AppSec handbook chapter using reviewer feedback in section-patch mode.

The original chapter is already valid. Do not rewrite it from scratch.

Generate only replacement Markdown for specific required sections that need improvement.

Do not append a new "Revision Additions" section.
Do not include editorial labels such as "Correction", "Enhancement", "Location", "Add after", or reviewer commentary.
Do not shorten the chapter.

Preserve the required handbook sections:
- Learning Objectives
- Conceptual Foundation
- Architecture Perspective
- AppSec Lens
- Developer Lens
- Pentest Lens
- Common Findings
- Secure Design Guidance
- Interview Questions
- Key Takeaways
- Sketchnote Placeholder

Use the review comments to improve technical accuracy, AppSec depth, clarity, interview questions, hallucination risk, and vendor-neutrality.

Return strictly valid JSON only:

```json
{
  "patches": [
    {
      "section": "Developer Lens",
      "content_markdown": "## Developer Lens\n\nReader-facing replacement content for this section."
    }
  ]
}
```

Each `content_markdown` value must start with the exact required section heading as a Markdown H2.
