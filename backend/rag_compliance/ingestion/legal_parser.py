"""
Deterministic structural parser for Indian Acts/Rules PDFs.

Replaces LLM-based (Ollama) chunk-boundary decisions and per-chunk metadata
tagging with a regex/state-machine parser that understands the actual
structure of these documents: numbered Sections/Rules, (1)(2)(3) sub-rules,
(a)(b)(c) clauses, "Provided that" provisos, and "Explanation.-" blocks.

Known limitation: the glyph-corruption filter below (`is_glyph_corrupted`)
catches one specific PDF font/CID-encoding corruption pattern observed in
this corpus (literal "/uniXXXX" tokens instead of real Unicode text). It is
not a general PDF-encoding-repair capability -- a differently-corrupted PDF
may not be caught by it.
"""

import os
import re
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Per-file act name / heading-label registry.
# Only used to LABEL a file's act/unit_label once it has been confirmed to
# structurally parse (>=1 heading match) -- routing itself is decided by
# match count, not filename, since filenames in this corpus are unreliable
# (e.g. "Ch9_Annexure_Rules_...pdf" is actually a form, not a Rules document).
ACT_REGISTRY = {
    "Companies Act 2013 as amended upto 01.04.2021_.pdf": {
        "act": "Companies Act, 2013",
        "unit_label": "Section",
    },
    "Companies (Incorporation) Rules, 2014 – consolidated.pdf": {
        "act": "Companies (Incorporation) Rules, 2014",
        "unit_label": "Rule",
    },
    "Companies (Accounts) Rules, 2014 – consolidated.pdf": {
        "act": "Companies (Accounts) Rules, 2014",
        "unit_label": "Rule",
    },
    "Companies (Appointment and Qualification of Directors) Rules, 2014 – consolidated.pdf": {
        "act": "Companies (Appointment and Qualification of Directors) Rules, 2014",
        "unit_label": "Rule",
    },
    "Companies (Management and Administration) Rules, 2014 – consolidated.pdf": {
        "act": "Companies (Management and Administration) Rules, 2014",
        "unit_label": "Rule",
    },
    "LLP Rules, 2009 – consolidated.pdf": {
        "act": "LLP Rules, 2009",
        "unit_label": "Rule",
    },
    "LLP_Act_PDF_Version_2_.pdf": {
        "act": "Limited Liability Partnership Act, 2008",
        "unit_label": "Section",
    },
}

MAX_SECTION_CHARS = 1200  # split larger sections at sub-section boundaries only

# Minimum heading-match count required to treat a file as a genuine
# structured Act/Rules document rather than routing it to the forms
# fallback splitter. Routing is content-based, not filename-based, because
# filenames in this corpus are unreliable (e.g. "Ch9_Annexure_Rules_...pdf"
# is actually Form AOC-4). A bare non-zero match count isn't enough on its
# own, though: forms with a handful of numbered fields (e.g. "1. Name of
# LLP") spuriously match the heading pattern a few times. Measured on this
# corpus: real Acts/Rules files have 67-627 heading matches; forms/misnamed
# annexures top out at 11. 20 sits cleanly in that gap.
MIN_SECTIONS_FOR_STRUCTURED_PARSE = 20

# Hard safety cap, independent of MAX_SECTION_CHARS. Most sections split
# cleanly at (1)(2)(3) sub-section boundaries, but some sections/rules in
# this corpus have no sub-section markers at all -- e.g. a Schedule/Annexure
# of dense unstructured prose embedded under one heading -- so the
# sub-section split has nothing to split on and the whole block would
# otherwise be emitted as one oversized chunk (observed up to ~21,000 chars
# in this corpus, which exceeds the local embedding model's context window
# and makes OllamaEmbeddings error out). Any chunk still over this size after
# structural splitting gets a final plain character-level split, keeping its
# section/subsection metadata intact across the resulting fragments.
HARD_MAX_CHARS = 3500
_size_fallback_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500, chunk_overlap=150, separators=["\n\n", "\n", ". ", " "],
)

# Title terminator differs by source: the Companies Act/Rules PDFs use an
# inline ".--" dash before the body starts on the same line ("160. Right of
# ...--(1) A person..."), while the LLP Act PDF has no trailing punctuation
# at all -- the title just ends at the line break ("48. Seizure of documents
# by inspector\n(1) Where..."). Match whichever terminator comes first.
HEADING_RE = re.compile(
    r"(?:^|\n)\s*(\d{1,4}[A-Z]?)\.\s+([A-Z][^.\n]{3,150}?)(?:\.—|(?=\n))",
    re.MULTILINE,
)
SUBSECTION_RE = re.compile(r"(?:^|\n)\s*\((\d{1,3})\)\s+")
CLAUSE_RE = re.compile(r"(?:^|\n)\s*\(([a-z]{1,2})\)\s+")
PROVISO_RE = re.compile(r"(?:^|\n)\s*Provided (?:that|further that|also that)\b")
EXPLANATION_RE = re.compile(r"(?:^|\n)\s*Explanation\s*\d*\s*[.:—-]")
CHAPTER_RE = re.compile(r"(?:^|\n)\s*CHAPTER\s+([IVXLCDM]+)\b")

GLYPH_TOKEN_RE = re.compile(r"/uni[0-9A-Fa-f]{4}")
BRACKET_NUM_RE = re.compile(r"(?<=\n)(\d{1,3})\[")
TOC_HEADING_RE = re.compile(r"(?:^|\n)\s*\d{1,4}[A-Z]?\.\s+[A-Z][^\n]{0,80}")
TOC_MARKER_RE = re.compile(r"ARRANGEMENT OF SECTIONS|\bCONTENTS\b", re.IGNORECASE)
DASH_VARIANTS_RE = re.compile(r"\.\s*(?:—|-|—|�)\s*(?=\n|[A-Z(])")


def is_glyph_corrupted(text: str, threshold: float = 0.05) -> bool:
    """Detect font/CID-encoding corruption producing literal /uniXXXX tokens."""
    if not text.strip():
        return False
    words = text.split()
    if not words:
        return False
    glyph_tokens = len(GLYPH_TOKEN_RE.findall(text))
    return (glyph_tokens / len(words)) > threshold


def is_toc_page(text: str) -> bool:
    """Detect a table-of-contents page: many short bare-number headings and
    no numbered sub-structure, or an explicit TOC marker."""
    if TOC_MARKER_RE.search(text):
        return True
    heading_matches = TOC_HEADING_RE.findall(text)
    if len(heading_matches) > 8 and not SUBSECTION_RE.search(text) and not CLAUSE_RE.search(text):
        return True
    return False


def _strip_amendment_brackets(text: str) -> str:
    """Remove leading digit+'[' and its matching ']' (amendment/insertion
    wrappers like '1[159. Penalty...]'), keeping the content inside."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        m = BRACKET_NUM_RE.match(text, i)
        if m:
            depth = 1
            j = m.end()
            while j < n and depth > 0:
                if text[j] == "[":
                    depth += 1
                elif text[j] == "]":
                    depth -= 1
                j += 1
            # emit inner content (between m.end() and j-1), skip the closing bracket
            out.append(text[m.end():max(j - 1, m.end())])
            i = j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _normalize_dashes(text: str) -> str:
    return DASH_VARIANTS_RE.sub(".—", text)


def _clean_for_parsing(text: str) -> str:
    text = _strip_amendment_brackets(text)
    text = _normalize_dashes(text)
    return text


def _reassemble(pages: list[Document]) -> tuple[str, list[tuple[int, int]]]:
    """Concatenate filtered pages into one string, tracking (char_offset, page_number)."""
    parts = []
    offsets = []
    cursor = 0
    for doc in pages:
        page_num = doc.metadata.get("page", 0)
        cleaned = _clean_for_parsing(doc.page_content)
        offsets.append((cursor, page_num))
        parts.append(cleaned)
        cursor += len(cleaned) + 1  # +1 for the join newline
    return "\n".join(parts), offsets


def _page_for_offset(offset: int, offsets: list[tuple[int, int]]) -> int:
    page = offsets[0][1] if offsets else 0
    for start, page_num in offsets:
        if start <= offset:
            page = page_num
        else:
            break
    return page


def _emit_section_chunks(section, act, unit_label, source, offsets):
    """Given one parsed section dict, emit one or more Document chunks."""
    full_text = section["text"].strip()
    number = section["number"]
    title = section["title"]
    chapter = section.get("chapter")
    page = _page_for_offset(section["start"], offsets)

    base_metadata = {
        "source": source,
        "act": act,
        "page": page,
        "chapter": chapter,
    }

    if len(full_text) <= MAX_SECTION_CHARS or not section["subsections"]:
        meta = dict(base_metadata)
        meta.update({
            "section": number,
            "subsection": None,
            "clause": None,
            "is_proviso": any(s["is_proviso"] for s in section["subsections"]),
            "is_explanation": any(s["is_explanation"] for s in section["subsections"]),
        })
        return [Document(page_content=full_text, metadata=meta)]

    # Oversized section: split at sub-section boundaries only.
    chunks = []
    header = f"{unit_label} {number}: {title}\n"
    for sub in section["subsections"]:
        sub_text = header + sub["text"].strip()
        sub_page = _page_for_offset(sub["start"], offsets)
        meta = dict(base_metadata)
        meta.update({
            "page": sub_page,
            "section": f"{number}({sub['number']})" if sub["number"] else number,
            "subsection": sub["number"],
            "clause": None,
            "is_proviso": sub["is_proviso"],
            "is_explanation": sub["is_explanation"],
            "parent_section_text": (title + ".—" + full_text[:300]),
        })
        chunks.append(Document(page_content=sub_text, metadata=meta))
    return chunks


def _parse_sections(text: str):
    """State-machine walk producing a list of section dicts."""
    headings = list(HEADING_RE.finditer(text))
    if not headings:
        return []

    chapters = list(CHAPTER_RE.finditer(text))

    def chapter_for(pos):
        current = None
        for m in chapters:
            if m.start() <= pos:
                current = m.group(1)
            else:
                break
        return current

    sections = []
    for idx, h in enumerate(headings):
        start = h.start()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        body = text[h.end():end]
        number = h.group(1)
        title = h.group(2).strip()

        subsections = _parse_subsections(body, start=h.end())
        sections.append({
            "number": number,
            "title": title,
            "start": start,
            "end": end,
            "text": text[start:end].strip(),
            "subsections": subsections,
            "chapter": chapter_for(start),
        })
    return sections


def _parse_subsections(body: str, start: int):
    """Within one section's body, split into (1)(2)(3) sub-units, attaching
    provisos/explanations to whichever sub-unit is currently open."""
    matches = list(SUBSECTION_RE.finditer(body))
    if not matches:
        return [{
            "number": None,
            "text": body,
            "start": start,
            "is_proviso": bool(PROVISO_RE.search(body)),
            "is_explanation": bool(EXPLANATION_RE.search(body)),
        }]

    subs = []
    for idx, m in enumerate(matches):
        sub_start = m.start()
        sub_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        sub_text = body[sub_start:sub_end]
        subs.append({
            "number": m.group(1),
            "text": sub_text,
            "start": start + sub_start,
            "is_proviso": bool(PROVISO_RE.search(sub_text)),
            "is_explanation": bool(EXPLANATION_RE.search(sub_text)),
        })

    # Any text before the first sub-section marker (e.g. a lead-in sentence)
    # is folded into the first sub-unit rather than dropped.
    lead_in = body[:matches[0].start()]
    if lead_in.strip():
        subs[0]["text"] = lead_in + subs[0]["text"]

    return subs


def parse_legal_pdf(pages: list[Document], source_path: str):
    """Parse one Act/Rule PDF's pages into hierarchical legal chunks.

    `source_path` is whatever the loader put in `doc.metadata["source"]`
    (may be a full path) -- it is stored verbatim in each chunk's `source`
    metadata for consistency with the rest of the pipeline, while the
    basename is used to look up the act/unit-label registry.

    Returns None if no top-level Section/Rule headings are found (signals
    the caller to fall back to the plain splitter for this file).
    """
    usable_pages = [p for p in pages if not is_toc_page(p.page_content)
                     and not is_glyph_corrupted(p.page_content)]
    if not usable_pages:
        return None

    text, offsets = _reassemble(usable_pages)
    sections = _parse_sections(text)
    if len(sections) < MIN_SECTIONS_FOR_STRUCTURED_PARSE:
        return None

    filename = os.path.basename(source_path)
    registry_entry = ACT_REGISTRY.get(filename, {})
    act = registry_entry.get("act", filename)
    unit_label = registry_entry.get("unit_label", "Section")

    chunks = []
    for section in sections:
        chunks.extend(_emit_section_chunks(section, act, unit_label, source_path, offsets))

    return [c for chunk in chunks for c in _enforce_size_cap(chunk)]


def _enforce_size_cap(chunk: Document) -> list[Document]:
    if len(chunk.page_content) <= HARD_MAX_CHARS:
        return [chunk]
    pieces = _size_fallback_splitter.split_text(chunk.page_content)
    return [Document(page_content=piece, metadata=dict(chunk.metadata)) for piece in pieces]
