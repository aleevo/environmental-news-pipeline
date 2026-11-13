
import re

from scripts.clean_article_text import clean_article_text
from scripts.subject_keywords import SUBJECT_KEYWORDS


def normalize_text(text):
    """
    Normalize text before keyword matching.

    This makes variations in whitespace, hyphens and
    ampersands more consistent.
    """

    if not isinstance(text, str):
        return ""

    text = clean_article_text(text)

    text = text.lower()

    # Normalize different hyphen types
    text = re.sub(r"[-–—‑]", " ", text)

    # Normalize ampersands
    text = text.replace("&", " and ")

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def find_keyword_matches(text, keywords):
    """
    Find keywords as complete words or phrases.

    Word boundaries help avoid accidental matches,
    such as matching 'star' inside an unrelated word.
    """

    matches = []

    for keyword in keywords:

        normalized_keyword = normalize_text(keyword)

        if not normalized_keyword:
            continue

        pattern = (
            r"(?<!\w)"
            + re.escape(normalized_keyword)
            + r"(?!\w)"
        )

        if re.search(pattern, text):
            matches.append(keyword)

    return matches


def predict_subjects_rule_based(title, summary):
    """
    Identify an article's scientific and environmental
    subject areas using keyword rules.

    Possible relevance statuses:
        strong_match
        partial_match
        no_match

    An article can match multiple subject areas.
    """

    # Normalize title and summary separately
    clean_title = normalize_text(title)
    clean_summary = normalize_text(summary)

    # Combine both fields for classification
    text = f"{clean_title} {clean_summary}".strip()

    subject_matches = []

    all_strong_matches = []
    all_supporting_matches = []

    # Examine every subject area
    for subject_area, keyword_groups in SUBJECT_KEYWORDS.items():

        strong_matches = find_keyword_matches(
            text,
            keyword_groups["strong"]
        )

        supporting_matches = find_keyword_matches(
            text,
            keyword_groups["supporting"]
        )

        # Only include subject areas with at least
        # one detected keyword
        if strong_matches or supporting_matches:

            subject_matches.append({
                "subject_area": subject_area,
                "strong_matches": strong_matches,
                "supporting_matches": supporting_matches
            })

            all_strong_matches.extend(strong_matches)
            all_supporting_matches.extend(supporting_matches)

    # Determine overall match strength
    if all_strong_matches:

        status = "strong_match"
        confidence = 0.85

    elif all_supporting_matches:

        status = "partial_match"
        confidence = 0.60

    else:

        status = "no_match"
        confidence = 0.50

    # Collect subject area names
    subject_areas = [
        item["subject_area"]
        for item in subject_matches
    ]

    # Build readable evidence
    if subject_matches:

        evidence_parts = []

        for item in subject_matches:

            details = []

            if item["strong_matches"]:
                details.append(
                    "strong: "
                    + ", ".join(item["strong_matches"])
                )

            if item["supporting_matches"]:
                details.append(
                    "supporting: "
                    + ", ".join(item["supporting_matches"])
                )

            evidence_parts.append(
                item["subject_area"]
                + " ("
                + "; ".join(details)
                + ")"
            )

        evidence = " | ".join(evidence_parts)

    else:

        evidence = "No recognised subject indicators"

    return {
        "relevance_status": status,
        "classification_method": "rule_based",
        "confidence_score": confidence,
        "subject_areas": subject_areas,
        "subject_matches": subject_matches,
        "evidence": evidence
    }

