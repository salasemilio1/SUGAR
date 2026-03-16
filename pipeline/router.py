"""
Router — Call 1 of 3.

Reads majors_registry.json and asks Gemini which major folder(s) are
relevant to the student's question. This call is fast and cheap because
it sends only the question and the small registry, not any documents.
"""

import json
import logging
from pathlib import Path

from pipeline.gemini_client import generate
from pipeline.prompts import router_prompt

log = logging.getLogger(__name__)

# ── Named constants ───────────────────────────────────────────────────────────

REGISTRY_FILENAME = "majors_registry.json"


# ── File I/O ──────────────────────────────────────────────────────────────────

def load_registry(base_path: str) -> dict:
    """Load the majors registry from the knowledge base directory.

    Args:
        base_path: Path to the knowledge_base directory.

    Returns:
        A dict mapping major slugs to their metadata.

    Raises:
        SystemExit: If the registry file is missing.
    """
    registry_path = Path(base_path) / REGISTRY_FILENAME

    if not registry_path.exists():
        log.error("Registry not found: %s", registry_path)
        print(
            f"\n✖  Could not find {REGISTRY_FILENAME} at:\n"
            f"   {registry_path.resolve()}\n"
            f"   This file maps department slugs to folder names.\n"
        )
        raise SystemExit(1)

    return json.loads(registry_path.read_text(encoding="utf-8"))


# ── Core routing ──────────────────────────────────────────────────────────────

def route(question: str, base_path: str) -> list[str]:
    """Identify which major folder(s) are relevant to a student's question.

    Args:
        question:  The student's question.
        base_path: Path to the knowledge_base directory.

    Returns:
        A list of major slug strings, e.g. ["computer_science"].
    """
    registry = load_registry(base_path)
    registry_json = json.dumps(registry, indent=2)

    prompt = router_prompt(question, registry_json)
    raw_response = generate(prompt)

    # Parse the JSON array from the LLM response
    try:
        slugs = json.loads(raw_response)

        if not isinstance(slugs, list):
            raise ValueError(f"Expected a JSON array, got: {type(slugs)}")

        # Validate that every slug actually exists in the registry
        valid_slugs = [s for s in slugs if s in registry]

        if not valid_slugs:
            log.warning(
                "LLM returned slugs not in registry: %s — falling back to all",
                slugs,
            )
            return list(registry.keys())

        return valid_slugs

    except (json.JSONDecodeError, ValueError) as exc:
        # If the LLM returns something unparseable, search everywhere
        log.warning(
            "Could not parse router response as JSON array: %s — "
            "falling back to all majors. Raw response: %s",
            exc,
            raw_response[:200],
        )
        return list(registry.keys())
