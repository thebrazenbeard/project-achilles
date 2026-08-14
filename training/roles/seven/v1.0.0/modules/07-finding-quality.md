# Module 07 — Security Finding Quality and Minimum Correction Oracles

## Learning objective
Produce findings that are reproducible, bounded, actionable, and independent of implementation authorship.

## Exercise
Invent one plausible security defect in a versioned CI-to-artifact publication system and write a Seven finding containing:
- stable finding ID;
- finding family;
- exact subject definition;
- severity and impact basis;
- violated invariant;
- minimum reproducer/hostile;
- observed result;
- why the evidence proves the defect;
- what is not proven;
- smallest acceptance correction oracle;
- regression hostile that must pass afterward;
- claim ceiling;
- dependencies/escalation.

Do not write the patch.

Then answer:
- When does a LOW/style issue reopen completed work?
- When does unresolved HIGH/MEDIUM block acceptance?
- What new evidence justifies reopening a closed finding?

## Pass criteria
Finding is independently reproducible; severity is evidence-based; correction oracle states properties rather than dictating implementation; unsupported claims are excluded; H/M-zero good-enough rule is correctly applied; historical closure is not reopened without material basis.
