#!/usr/bin/env python3
"""
loop_decoder.py — Extract text content from Microsoft Loop (.loop) files.

Usage:
    python3 loop_decoder.py <file.loop>
    python3 loop_decoder.py <file.loop> --output <output.md>
    python3 loop_decoder.py <dir/>              # batch process all .loop files

Output: a .md file saved next to the source file (or at --output path).
"""

import zlib
import re
import sys
import argparse
from pathlib import Path

# Section names that become H2 headings in meeting-note Loop templates.
_KNOWN_H2 = {
    "Agenda", "Meeting notes", "Follow-up tasks",
    "Decisions", "Open questions", "Goals", "Action items",
}

# Texts that are UI chrome / framework metadata and should be dropped entirely.
_SKIP_EXACT = {
    "AI-generated content in notes may be incorrect.",
    "AI-generated content in notes may be incorrect. ",
    "Learn more", "Task", "Bucket", "Due date", "Assigned to", "Planner Task Id",
}


def decompress_all_gzip_blocks(data: bytes) -> list[str]:
    """Find and decompress every gzip block in the binary data."""
    blocks = []
    pos = 0
    magic = b"\x1f\x8b"

    while True:
        idx = data.find(magic, pos)
        if idx == -1:
            break
        # Try largest sizes first so we capture full blocks, not truncated ones
        for size in [len(data) - idx, 50000, 10000, 5000, 2000, 1000, 500]:
            try:
                d = zlib.decompressobj(zlib.MAX_WBITS | 16)
                text = d.decompress(data[idx : idx + size]).decode("utf-8", errors="replace")
                blocks.append(text)
                break
            except Exception:
                pass
        pos = idx + 1

    return blocks


def extract_text_from_blocks(blocks: list[str]) -> tuple[list[str], list[str]]:
    """
    Pull ordered text from segmentTexts chunks.
    Returns (primary_texts, followup_texts).
    - primary_texts: from the main document body (highest chunkSegmentCount)
    - followup_texts: from secondary blocks not already in primary (task table items)
    """
    candidates = []
    for block in blocks:
        if '"segmentTexts"' not in block:
            continue
        count_match = re.search(r'"chunkSegmentCount"\s*:\s*(\d+)', block)
        count = int(count_match.group(1)) if count_match else 0
        texts = re.findall(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', block)
        if texts:
            candidates.append((count, texts))

    if not candidates:
        return [], []

    # Sort by segment count descending — main document body has the most segments
    candidates.sort(key=lambda x: x[0], reverse=True)

    # Primary source
    _, primary_texts_raw = candidates[0]
    seen = set()
    primary_texts = []
    for t in primary_texts_raw:
        t = t.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\").strip()
        if t and t not in seen and not _is_metadata(t):
            seen.add(t)
            primary_texts.append(t)

    # Secondary blocks: collect texts not already in primary (likely task table items)
    followup_texts = []
    followup_seen = set(seen)
    for _, texts_raw in candidates[1:]:
        for t in texts_raw:
            t = t.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\").strip()
            if t and t not in followup_seen and not _is_metadata(t):
                followup_seen.add(t)
                followup_texts.append(t)

    return primary_texts, followup_texts


def _is_metadata(text: str) -> bool:
    """Filter out internal framework strings and UI chrome."""
    skip_prefixes = ("__fluid", "/", "http", "%css", "en-us", "ltr", "Plain", "StoryNode")
    return text.startswith(skip_prefixes) or text in _SKIP_EXACT


def _is_subheading(text: str) -> bool:
    """
    Heuristic: topic sub-headings are short (1–6 words), contain at least one
    uppercase letter, and have no trailing sentence-ending punctuation.
    """
    words = text.split()
    return (
        1 <= len(words) <= 6
        and len(text) < 60
        and not text.endswith(".")
        and not text.endswith(",")
        and not text.endswith("?")
        and sum(1 for c in text if c.isupper()) >= 1
    )


def extract_text_from_ops_log(blocks: list[str]) -> list[dict]:
    """
    Fallback extractor for Loop files where content is stored in the Fluid
    Framework ops log rather than in snapshot segmentTexts chunks.

    This format appears in newer Loop files.  The ops log is the largest gzip
    block and contains double-escaped JSON op messages of the form:

        \\"pos1\\":N,\\"seg\\":{\\"text\\":\\"<content>\\",\\"props\\":{...}}

    Returns a list of dicts — [{text, kind}, ...] in ops-log order, which
    approximates the visual document order.  kind is one of "H2", "H3", "BODY".
    """
    # Identify the ops-log block: large, contains sequence numbers + clientId ops.
    ops_block = None
    for block in sorted(blocks, key=len, reverse=True):
        if '"sequenceNumber"' in block and '"clientId"' in block and len(block) > 10000:
            ops_block = block
            break

    if ops_block is None:
        return []

    seg_pattern = re.compile(
        r'\\"pos1\\":\s*(\d+),\\"seg\\":\s*\{\\"text\\":\s*\\"(.*?)\\",',
        re.DOTALL,
    )

    entries = []
    for m in seg_pattern.finditer(ops_block):
        text = m.group(2)
        text = (
            text
            .replace('\\"', '"')
            .replace('\\n', '\n')
            .replace('\\\\', '\\')
            .replace('\\u2014', '\u2014')
            .replace('\\u201c', '\u201c')
            .replace('\\u201d', '\u201d')
            .strip()
        )

        if not text or text in _SKIP_EXACT or _is_metadata(text):
            continue

        # Classify: check the next 400 chars of context for targetLabel (structural
        # section anchors inserted by the Loop template engine).
        ctx = ops_block[m.start(): m.start() + 400]
        has_target_label = bool(re.search(r'\\"targetLabel\\"', ctx[:300]))

        if text in _KNOWN_H2 or has_target_label:
            kind = "H2"
        elif _is_subheading(text):
            kind = "H3"
        else:
            kind = "BODY"

        entries.append({"text": text, "kind": kind})

    return entries


def ops_log_to_markdown(entries: list[dict], source_path: Path) -> str:
    """
    Convert ops-log entries into structured Markdown.

    H2 entries become ## headings, H3 entries become ### headings, and BODY
    entries become bullet points.  An AI-accuracy disclaimer is inserted after
    the "Meeting notes" heading if present.
    """
    lines = [f"# {source_path.stem}", ""]
    ai_note_added = False

    for e in entries:
        text, kind = e["text"], e["kind"]

        if kind == "H2":
            lines.append(f"## {text}")
            lines.append("")
            if text.lower() == "meeting notes" and not ai_note_added:
                lines.append("*AI-generated content — may be inaccurate.*")
                lines.append("")
                ai_note_added = True
        elif kind == "H3":
            lines.append(f"### {text}")
            lines.append("")
        else:
            lines.append(f"- {text}")

    lines.append("")
    return "\n".join(lines) + "\n"


def texts_to_markdown(texts: list[str], followup_texts: list[str], source_path: Path) -> str:
    """
    Convert the flat list of extracted text segments into structured Markdown.
    Headings are detected by style (short, no period, title-case or all-cap words).
    followup_texts are appended under ## Follow-up tasks if not already in primary.
    """
    heading_patterns = [
        "Decisions",
        "Open questions",
        "Meeting notes",
        "Follow-up tasks",
        "Agenda",
        "Goal",
    ]

    lines = []
    lines.append(f"# {source_path.stem}")
    lines.append("")

    i = 0
    while i < len(texts):
        t = texts[i]

        # Top-level section heading
        if any(t.lower().startswith(h.lower()) for h in heading_patterns):
            lines.append(f"## {t}")
            lines.append("")
            i += 1
            continue

        # Sub-heading: short (≤6 words), no trailing period, not a sentence
        words = t.split()
        is_subheading = (
            2 <= len(words) <= 6
            and not t.endswith(".")
            and not t.endswith(",")
            and sum(1 for c in t if c.isupper()) >= 1
            and i > 0
        )
        if is_subheading and len(t) < 60:
            lines.append(f"### {t}")
            lines.append("")
            i += 1
            continue

        # Regular content
        lines.append(f"- {t}")
        i += 1

    # Append task table items only if primary body doesn't already have a Follow-up tasks section
    primary_has_followup = any("follow-up tasks" in t.lower() for t in texts)
    if followup_texts and not primary_has_followup:
        lines.append("")
        lines.append("## Follow-up tasks")
        lines.append("")
        for t in followup_texts:
            lines.append(f"- {t}")

    return "\n".join(lines) + "\n"


def decode_loop_file(input_path: Path, output_path: Path | None = None) -> Path:
    """Decode a single .loop file and write a .md file.

    Tries two extraction strategies in order:
    1. Snapshot segmentTexts (older / simpler Loop files).
    2. Fluid ops-log (newer Loop files where text lives in the ops stream).
    """
    if output_path is None:
        output_path = input_path.with_suffix(".md")

    data = input_path.read_bytes()
    blocks = decompress_all_gzip_blocks(data)

    # Strategy 1 — snapshot segmentTexts
    texts, followup_texts = extract_text_from_blocks(blocks)
    if texts or followup_texts:
        md = texts_to_markdown(texts, followup_texts, input_path)
        output_path.write_text(md, encoding="utf-8")
        return output_path

    # Strategy 2 — ops-log fallback
    entries = extract_text_from_ops_log(blocks)
    if entries:
        md = ops_log_to_markdown(entries, input_path)
        output_path.write_text(md, encoding="utf-8")
        return output_path

    raise ValueError(f"No text content found in {input_path}")


def main():
    parser = argparse.ArgumentParser(description="Decode Microsoft Loop (.loop) files to Markdown.")
    parser.add_argument("input", help=".loop file or directory containing .loop files")
    parser.add_argument("--output", "-o", help="Output .md file path (single file mode only)")
    args = parser.parse_args()

    input_path = Path(args.input)

    # Batch mode: directory
    if input_path.is_dir():
        loop_files = list(input_path.glob("*.loop"))
        if not loop_files:
            print(f"No .loop files found in {input_path}")
            sys.exit(1)
        for f in loop_files:
            try:
                out = decode_loop_file(f)
                print(f"  decoded: {f.name} -> {out.name}")
            except Exception as e:
                print(f"  failed:  {f.name} — {e}")
        return

    # Single file mode
    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else None

    try:
        out = decode_loop_file(input_path, output_path)
        print(f"Saved: {out}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
