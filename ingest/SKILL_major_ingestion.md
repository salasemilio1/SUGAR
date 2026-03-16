# SKILL: Major Skills File Generator
# Southwestern University — Knowledge Assistant Ingestion Pipeline
# Version: 1.0
# Last Updated: 2025-03-14

---

## Purpose

This skill guides a frontier AI model (Claude Sonnet or Opus recommended) through
the process of reading extracted text files from a university major's document
corpus and producing a structured `skills_index.md` file for that major.

The `skills_index.md` is the backbone of the inference pipeline. It is the ONLY
file the routing model reads before deciding which documents to retrieve. Everything
downstream — routing accuracy, answer quality, fallback behavior — depends on the
quality of this file. Treat its generation as the highest-value step in the system.

---

## System Context

### Architecture Overview

This skills file is part of a two-phase AI knowledge assistant built for
Southwestern University students.

**Phase 1 — Ingestion (this skill)**
A frontier model reads all `.txt` files for a given major and produces a
`skills_index.md`. This runs once, offline, and is regenerated only when
source documents are updated.

**Phase 2 — Inference (downstream)**
When a student asks a question, the inference model:
1. Reads the `skills_index.md` for the student's major
2. Makes a routing decision: which 1-3 `.txt` files contain the answer
3. Loads those files into context
4. Answers the student's question with citations

The routing model reads the skills index cold — it has no memory of previous
queries and no access to the raw documents at routing time. Every routing
decision lives or dies on the quality of this index.

### File System Layout

```
/knowledge_base
  /<major_slug>                    ← e.g., computer_science
    skills_index.md                ← THIS FILE (output of ingestion)
    /docs
      /raw                         ← original PDFs (source of truth)
      /extracted                   ← .txt files (input to ingestion)
  /general                         ← university-wide policies
    skills_index.md
    /docs
      /raw
      /extracted
```

### Input Format

The model receives `.txt` files extracted from PDFs via `pdfplumber`.
Each file has page separators in the format:

```
--- Page N of Total ---

[page content]
```

Tables may be imperfectly formatted. Course numbers, credit hours, and
prerequisite chains are the most critical data — verify them carefully
against surrounding context when the table formatting looks degraded.

---

## Ingestion Prompt

Use the following prompt verbatim when calling the frontier model. Replace
bracketed placeholders before sending.

---

```
You are an expert academic document analyst building a structured index for
a university AI knowledge assistant at Southwestern University in Georgetown, Texas.

Your task is to read all provided documents for the [MAJOR_NAME] department
and produce a `skills_index.md` file in the exact format specified below.

This index will be used by an AI routing model that has NO access to the
original documents. The routing model reads ONLY this index, then decides
which documents to retrieve. If a topic, course, or policy is not captured
here, the system cannot retrieve it. Omissions are silent failures.

Be exhaustive. Be specific. Use exact course numbers, credit hour counts,
and policy language from the documents. Do not generalize when exact
information is available.

--- INPUT DOCUMENTS ---

[DOCUMENT 1]
Filename: [exact_filename.txt]
[full extracted text content]

[DOCUMENT 2]
Filename: [exact_filename.txt]
[full extracted text content]

[... repeat for all documents ...]

--- END DOCUMENTS ---

Produce the skills_index.md now, following this structure exactly:

════════════════════════════════════════════════════════
SECTION 1 — METADATA BLOCK
════════════════════════════════════════════════════════

# Skills Index — [MAJOR_NAME]
**Institution:** Southwestern University, Georgetown, Texas
**Last Ingested:** [DATE]
**Ingestion Model:** [MODEL_NAME]
**Document Count:** [N]
**Degree Paths Covered:** [e.g., B.S., B.A., Minor]

---

════════════════════════════════════════════════════════
SECTION 2 — DOCUMENT REGISTRY
════════════════════════════════════════════════════════

For EVERY .txt file provided, produce one entry in this format.
Do not skip any file. The filename must match exactly as provided.

### [Human-Readable Document Title]
- **filename:** `exact_filename.txt`
- **document_type:** [one of: requirements | course_info | policy | advising | calendar | financial | general]
- **degree_relevance:** [one or more of: B.S. | B.A. | Minor | All | General]
- **time_sensitive:** [true | false]
- **catalog_year:** [e.g., 2024-2025 — or "N/A" if not time-sensitive]
- **description:** [5-7 sentences. Be specific. Name the actual courses,
  requirement categories, policies, credit hour counts, and GPA thresholds
  mentioned. A generic description like "covers CS requirements" is a failure.
  A good description names every major section of the document.]
- **critical_data:** [Bullet list of the most important specific facts in this
  document — things a student would directly ask about. Examples: total credit
  hours, specific required courses, GPA cutoffs, deadlines, named policies.]
- **retrieval_triggers:** [10-15 short phrases that represent student queries
  this document can answer. These are used by the routing model for fuzzy
  matching. Write them as a student would say them, not as a librarian would
  catalog them. Examples: "how many credits to graduate", "do I need calc",
  "what counts as an elective"]

---

════════════════════════════════════════════════════════
SECTION 3 — DEGREE PATH SUMMARIES
════════════════════════════════════════════════════════

Write a structured summary for each degree path available in this major.
This section is the most frequently retrieved section for broad advising
questions. Be complete — do not omit any requirement category.

For each degree path (B.S., B.A., Minor, etc.):

### [Degree Path Name] — e.g., B.S. in Computer Science

| Field | Detail |
|---|---|
| Total Credit Hours | |
| Major Credit Hours | |
| Minimum GPA (Overall) | |
| Minimum GPA (Major) | |
| Residency Requirement | |
| Source Document | `filename.txt` |

**Required Core Courses:**
List every required course with course number, full name, and credit hours.
Example: CSCI 1320 — Introduction to Programming (3 hrs)

**Required Supporting Courses (Math, Science, etc.):**
[same format]

**Elective Requirements:**
- How many credit hours of electives required:
- Pool of eligible courses (list all, with numbers):
- Any restrictions on elective selection:

**Concentration or Track Options (if any):**
[describe each track and its specific requirements]

**Additional Graduation Requirements:**
[capstone, internship, portfolio, senior seminar, etc.]

**Notable Constraints:**
[anything unusual — time limits, sequential requirements, GPA gates, etc.]

---

Repeat the above block for every degree path. Then add:

### Key Differences Between Degree Paths

This subsection is REQUIRED and must be explicit. The most common student
routing failure is a question about "the CS degree" without specifying B.S.
vs B.A. The routing model must be able to identify when this disambiguation
is needed.

- List every meaningful difference between the B.S. and B.A. (or other paths)
- Include: credit hour differences, required courses that differ, elective
  flexibility differences, math/science requirement differences
- Note which path is more common or recommended for specific career goals
  if the documents indicate this

---

════════════════════════════════════════════════════════
SECTION 4 — COURSE INDEX
════════════════════════════════════════════════════════

List every course mentioned across ALL documents. This section is retrieved
when a student asks about a specific course. Accuracy of prerequisites is
critical — an error here directly harms student scheduling decisions.

For each course:

### CSCI XXXX — [Course Name]
- **Credit Hours:** 
- **Prerequisites:** [list exactly as stated in documents, or "None"]
- **Corequisites:** [if any, or "None"]
- **Offered:** [Fall | Spring | Both | Unknown]
- **Required For:** [which degree paths require this course]
- **Counts As:** [requirement category it satisfies — e.g., "Core requirement", "Upper-division elective"]
- **Notes:** [any enrollment restrictions, lab components, special considerations]
- **Source:** `filename.txt`

Group courses by prefix if multiple prefixes exist (e.g., CSCI, MATH, PHYS).

---

════════════════════════════════════════════════════════
SECTION 5 — TOPIC INDEX
════════════════════════════════════════════════════════

This is the primary routing lookup table. The routing model scans this
section to match a student query to relevant documents.

Produce 50-80 entries. Err on the side of more. Granularity matters —
"elective requirements" and "upper-division elective requirements" are
different topics and may map to different documents.

Format each entry as:
- [specific topic] → `filename.txt` [, `filename2.txt` if multiple]

Required topic categories to cover at minimum:
- All degree path variations and differences
- Every named requirement category from every degree path
- All individual required courses (by course number AND by name)
- Course substitution and waiver policies
- Transfer credit evaluation
- GPA requirements — overall, major GPA if different, GPA for honors
- Academic standing, probation, dismissal
- Graduation application process and timeline
- Prerequisite chains for upper-division courses
- Double major / dual degree policies
- Adding or dropping the minor
- Senior capstone or culminating requirement
- Advising requirements and appointment processes
- Course repeat policies
- Pass/fail grading options
- Incomplete grade policies
- Academic calendar and registration deadlines
- Study abroad credit applicability
- Internship or experiential learning credit

---

════════════════════════════════════════════════════════
SECTION 6 — QUERY PATTERN MAP
════════════════════════════════════════════════════════

Generate 35 realistic student questions. These give the routing model
concrete examples to reason against. Cover the full student lifecycle
and all degree paths. Include ambiguous questions that require
disambiguation.

For each entry:

**Q:** [the student's question, written naturally as a student would ask it]
**Docs:** `filename.txt` [, `filename2.txt`]
**Routing Note:** [one sentence: what in the index led to this routing decision,
and what part of the document answers it]
**Disambiguation Needed:** [Yes/No — if Yes, what must the system clarify before answering]

Cover questions from each of these student profiles:
- Incoming freshman (first semester, no prior coursework)
- Sophomore deciding between B.S. and B.A.
- Junior considering adding the minor
- Senior applying for graduation
- Transfer student evaluating credit applicability
- Student who failed or withdrew from a required course
- Student considering a double major
- Student with an academic hold or GPA concern
- Student asking about a specific course (at least 5 course-specific questions)
- Student asking a question where the answer requires BOTH the major doc
  AND a general university policy doc (at least 3 such questions)

---

════════════════════════════════════════════════════════
SECTION 7 — CROSS-REFERENCE FLAGS
════════════════════════════════════════════════════════

List every topic where this major's documents are INCOMPLETE and a complete
answer requires consulting the /general university policy documents.

For each flag:

- **Topic:** [topic name]
- **What major docs cover:** [what partial information exists in major docs]
- **What general docs must cover:** [what is missing and must come from /general]
- **Routing instruction:** [e.g., "Always retrieve both `cs_requirements.txt`
  AND a general policy document when this topic appears in a query"]

Common cross-reference flags to watch for:
- Academic withdrawal and refund deadlines
- Grade appeal procedures
- Financial aid impact of credit load changes
- Academic probation and dismissal appeals
- Leave of absence policies
- Disability accommodations process
- Graduation honors (Latin honors) GPA thresholds
- Veterans benefits and enrollment certification

---

════════════════════════════════════════════════════════
SECTION 8 — KNOWN GAPS
════════════════════════════════════════════════════════

List every topic a student might reasonably ask that CANNOT be answered
from the provided documents. Be honest. This section drives the system's
fallback responses — an unanswered question is far better than a
hallucinated answer.

For each gap:

- **Topic:** [what the student might ask]
- **Reason for gap:** [not in any provided document | likely in general docs | may require advisor]
- **Recommended fallback:** [e.g., "Direct student to academic advisor",
  "Direct student to registrar's office", "Check /general document set"]

---

════════════════════════════════════════════════════════
SECTION 9 — ROUTING DECISION GUIDE
════════════════════════════════════════════════════════

This section is written FOR the routing model, not for humans. It provides
explicit decision logic the routing model should follow for this major.

**Default document for broad major questions:** `[filename.txt]`

**When to retrieve multiple documents:**
[list specific conditions — e.g., "Any question about course substitution
requires both `requirements.txt` and `policies.txt`"]

**Degree path disambiguation triggers:**
[list phrases or patterns in student queries that signal the routing model
must ask a clarifying question before retrieving — e.g., "If student says
'the CS degree' without specifying B.S. or B.A., ask which they mean before
routing"]

**High-confidence single-document retrievals:**
[list topics that definitively map to exactly one document]

**Always escalate to human advisor:**
[list any question types that should never be answered by the AI alone —
e.g., exceptions to policy, academic appeals, financial decisions]

---

End of skills_index.md. Do not include any text after Section 9.
```

---

## Post-Generation Validation Checklist

After the model returns the skills index, verify the following before
saving the file to the file system. This takes 10-15 minutes and
prevents silent routing failures downstream.

### Document Registry
- [ ] Every `.txt` file in `/docs/extracted/` appears exactly once in Section 2
- [ ] No filename is misspelled or has wrong extension
- [ ] Every description names specific courses, credit hours, or policies
      (reject any description that could apply to any university document)
- [ ] `retrieval_triggers` read like student questions, not catalog entries

### Degree Path Summaries
- [ ] Total credit hours match the source document exactly
- [ ] Every required course is listed with correct course number and credit hours
- [ ] B.S. vs B.A. differences section is present and explicit
- [ ] GPA requirements are captured (both overall and major GPA if different)

### Course Index
- [ ] Spot-check 5 random courses: verify prerequisites against source `.txt`
- [ ] No course listed as having "None" prerequisites when the source shows otherwise
- [ ] All courses required for graduation appear in the index

### Topic Index
- [ ] Count entries — should be 50 minimum, 80 preferred
- [ ] Every required course appears as its own topic entry by course number
- [ ] Transfer credit, substitution, and waiver policies are present

### Query Pattern Map
- [ ] At least 3 questions require both major and /general documents
- [ ] At least one question per student profile listed in the prompt
- [ ] At least 5 course-specific questions present

### Known Gaps
- [ ] Honest — does not omit gaps because they are embarrassing
- [ ] Every gap has a specific recommended fallback action

---

## Re-ingestion Trigger Conditions

Re-run ingestion (and regenerate the skills index) when any of the
following occur:

- A new academic catalog year is published
- Any degree requirements change
- New courses are added or removed from the major
- A prerequisite chain changes
- University-wide policies referenced in major documents are updated
- A new document is added to `/docs/raw/`
- Manual review identifies errors in the existing skills index

After re-ingestion, commit the updated `skills_index.md` to version
control and diff against the previous version to verify changes are
accurate and complete.

---

## Notes on Southwestern University Context

- SU is a small liberal arts university — degree plans may emphasize
  interdisciplinary requirements more than large research universities
- The university uses a semester system
- Catalog year is critical context — always confirm which catalog year
  the documents belong to and note it in the metadata block
- SU's CS department offers B.S., B.A., and Minor — all three paths
  must be captured even if they share a single source document
- Course numbering convention: confirm the prefix (CSCI, CS, etc.)
  from the actual documents — do not assume
- Small department means some courses may have irregular offering
  schedules (every other year, etc.) — capture this if present
