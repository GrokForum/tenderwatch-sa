"""CHG-TW-006: scans run over every generated public file before it may be published.

Each scan returns a list of findings (file and kind, never the matched personal
value itself). An empty list is a pass. Standard library only.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

ROLE_EMAIL = "privacy@grokforum.site"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# SA phone numbers: +27 or 0, then 9 digits, optional spaces or hyphens between groups.
SA_PHONE_RE = re.compile(r"(?<![0-9])(?:\+27|0027|0)[\s-]?[1-9][0-9][\s-]?[0-9]{3}[\s-]?[0-9]{4}(?![0-9])")
SA_ID_RE = re.compile(r"(?<![0-9])[0-9]{13}(?![0-9])")
# Street-address shapes: a house number then a street word.
ADDRESS_RE = re.compile(
    r"(?i)\b[0-9]{1,5}[A-Za-z]?\s+(?:[A-Z][a-z]+\s+){1,3}"
    r"(?:street|str|road|rd|avenue|ave|drive|crescent|lane|close|way|boulevard|place)\b"
)
PRIVATE_PATH_RE = re.compile(r"/home/[a-z]|/workspace\b|/cursor/|/tmp/|/root/|\\Users\\")
# AI product and vendor names that must not appear in public files. "GrokForum" (the responsible party) is
# allowed; a bare "Grok" is not. Project-specific agent names are not committed: they are read from the
# git-ignored file data/local/public_scan_extra_terms.txt (one term per line), if it exists.
BOT_NAME_RE = re.compile(r"(?i)\b(?:grok(?!\s*forum)\w*|claude|chatgpt|openai|anthropic|copilot)\b")
EXTRA_TERMS_PATH = Path(__file__).resolve().parents[1] / "data" / "local" / "public_scan_extra_terms.txt"


def extra_terms(path: Path | None = None) -> list[str]:
    p = path or EXTRA_TERMS_PATH
    if not p.is_file():
        return []
    return [t.strip() for t in p.read_text(encoding="utf-8").splitlines() if t.strip() and not t.startswith("#")]


# Wording grep: accusatory or loaded words never used about a supplier, and the
# bare label "Reported" without ", Unconfirmed" (owner rule, CHG-TW-004 §13.7).
LOADED_WORDS_RE = re.compile(
    r"(?i)\b(?:corrupt\w*|fraud\w*|suspicious\w*|suspect\w*|irregular\w*|dodgy|crook\w*|"
    r"red[\s-]?flags?|shell\s+compan\w+|front(?:ing|s)?\s+compan\w+|tenderpreneur\w*|"
    r"looting|kickbacks?|bribe\w*|scam\w*|guilty|wrongdoer\w*|criminal\w*|rigged)\b"
)
BARE_REPORTED_RE = re.compile(r"\bReported\b(?!, Unconfirmed)")
# Phrases that are allowed although they contain a loaded word: they deny it.
ALLOWED_PHRASES = (
    "not a finding that anyone did anything wrong",
)

TEXT_SUFFIXES = {".html", ".txt", ".csv", ".json", ".md", ""}


def public_files(root: Path) -> list[Path]:
    """Every file under root, except a .git directory."""
    return sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts)


def _text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def scan_pii(files: Iterable[Path], root: Path) -> list[str]:
    out: list[str] = []
    for p in files:
        t = _text(p)
        rel = p.relative_to(root).as_posix()
        for m in EMAIL_RE.finditer(t):
            if m.group(0).lower() != ROLE_EMAIL:
                out.append(f"{rel}: email other than the role address")
        if SA_PHONE_RE.search(t):
            out.append(f"{rel}: SA phone number shape")
        if SA_ID_RE.search(t):
            out.append(f"{rel}: 13-digit number (SA ID shape)")
        if ADDRESS_RE.search(t):
            out.append(f"{rel}: street-address shape")
    return out


def scan_paths_and_bot_names(files: Iterable[Path], root: Path, extra: Iterable[str] | None = None) -> list[str]:
    terms = [t.casefold() for t in (extra_terms() if extra is None else extra)]
    out: list[str] = []
    for p in files:
        t = _text(p)
        rel = p.relative_to(root).as_posix()
        if PRIVATE_PATH_RE.search(t):
            out.append(f"{rel}: private path")
        if BOT_NAME_RE.search(t) or any(term in t.casefold() for term in terms):
            out.append(f"{rel}: bot, agent or product name")
    return out


def scan_wording(files: Iterable[Path], root: Path) -> list[str]:
    out: list[str] = []
    for p in files:
        t = _text(p)
        for phrase in ALLOWED_PHRASES:
            t = t.replace(phrase, "")
        rel = p.relative_to(root).as_posix()
        m = LOADED_WORDS_RE.search(t)
        if m:
            out.append(f"{rel}: loaded word ({m.group(0)!r})")
        if BARE_REPORTED_RE.search(t):
            out.append(f"{rel}: bare 'Reported' label without ', Unconfirmed'")
    return out


def _strip_allowed(text_up: str, allowed_up: list[str]) -> str:
    for a in allowed_up:  # longest first, so a shorter shown name never splits a longer one
        text_up = text_up.replace(a, "\x00")
    return text_up


def scan_names(files: Iterable[Path], root: Path, names: Iterable[str], allowed: Iterable[str] = (), *,
               conflicts_are_findings: bool = True) -> list[str]:
    """Case-insensitive search for each name, after removing the names the register shows (allowed).

    With conflicts_are_findings (the withheld-name scan), a name that is itself in allowed is reported:
    a withheld name must never also be shown. Findings give the file and a
    count, never the name.
    """
    allowed_up = sorted({a.strip().upper() for a in allowed if a and a.strip()}, key=len, reverse=True)
    wanted = {n.strip().upper() for n in names if n and n.strip()}
    out: list[str] = []
    conflicts = wanted & set(allowed_up)
    if conflicts and conflicts_are_findings:
        out.append(f"{len(conflicts)} name(s) are both shown and on the scan list")
    wanted -= set(allowed_up)
    for p in files:
        t = _text(p).upper()
        # HTML escapes the ampersand and apostrophe; search the unescaped form.
        t = t.replace("&AMP;", "&").replace("&#X27;", "'").replace("&#39;", "'").replace("&QUOT;", '"')
        t = _strip_allowed(t, allowed_up)
        hits = sum(1 for n in wanted if n in t)
        if hits:
            out.append(f"{p.relative_to(root).as_posix()}: {hits} name(s) that must not be published")
    return out


def run_all(root: Path, *, withheld: Iterable[str], all_names: Iterable[str], allowed: Iterable[str]) -> dict[str, list[str]]:
    """All public-file scans. withheld: the 198-name set; all_names: the 718-name set; allowed: names the
    register shows unmasked (the only names from all_names that may appear)."""
    files = public_files(root)
    allowed = list(allowed)
    return {
        "names_withheld": scan_names(files, root, withheld, allowed),
        "names_all_except_shown": scan_names(files, root, all_names, allowed, conflicts_are_findings=False),
        "pii": scan_pii(files, root),
        "paths_and_bot_names": scan_paths_and_bot_names(files, root),
        "wording": scan_wording(files, root),
    }
