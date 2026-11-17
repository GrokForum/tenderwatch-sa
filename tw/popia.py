"""Drop and detect personal-information keys that must not reach the warehouse or export."""
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

from tw.normalise import SA_ID_RE

# Key names (case-insensitive, ignoring underscores) that must never be stored.
_FORBIDDEN_KEY_FOLDS = {
    "contactpoint",
    "contactperson",
    "email",
    "emailaddress",
    "telephone",
    "phone",
    "phonenumber",
    "fax",
    "faxnumber",
    "mobile",
    "cell",
    "streetaddress",
    "physicaladdress",
    "postaladdress",
    "addressline1",
    "addressline2",
    "addressline3",
    "postalcode",
    "postcode",
    "zipcode",
    "said",
    "saidnumber",
    "idnumber",
    "identitynumber",
    "passport",
    "passportnumber",
    "directorid",
    "homeaddress",
    "residentialaddress",
}

# "address" itself is forbidden as a key, but we allow source_url-like fields.
_FORBIDDEN_EXACT = {"address"}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _fold_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def is_forbidden_key(key: str) -> bool:
    k = key.lower()
    if k in _FORBIDDEN_EXACT:
        return True
    return _fold_key(key) in _FORBIDDEN_KEY_FOLDS


def strip_forbidden(obj: Any, keep_country: bool = True) -> Any:
    """Recursively drop forbidden keys from dicts/lists.

    `parties.address` is dropped entirely. A lone `country` / `countryName`
    is allowed only if it is not nested under an address we already dropped
    (we drop the address object as a whole).
    """
    if isinstance(obj, Mapping):
        out = {}
        for k, v in obj.items():
            if is_forbidden_key(str(k)):
                continue
            out[k] = strip_forbidden(v, keep_country=keep_country)
        return out
    if isinstance(obj, list):
        return [strip_forbidden(x, keep_country=keep_country) for x in obj]
    return obj


def find_forbidden_keys(obj: Any, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            if is_forbidden_key(str(k)):
                hits.append(p)
            hits.extend(find_forbidden_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(find_forbidden_keys(v, f"{path}[{i}]"))
    return hits


def find_id_or_contact_leaks(obj: Any, path: str = "") -> list[str]:
    """Scan string values for SA ID numbers or emails (tests fail on a hit)."""
    hits: list[str] = []
    if isinstance(obj, Mapping):
        # Keys already checked separately; skip source URLs for email-like paths
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            hits.extend(find_id_or_contact_leaks(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(find_id_or_contact_leaks(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        if SA_ID_RE.search(obj):
            hits.append(f"sa_id:{path}")
        # Do not flag emails inside official source URLs / documentation links
        if EMAIL_RE.search(obj) and not path.endswith(("_url", "source_url", "source")):
            hits.append(f"email:{path}")
    return hits


def assert_clean(records: Iterable[Mapping], *, context: str) -> None:
    recs = list(records)
    key_hits = []
    leak_hits = []
    for i, rec in enumerate(recs):
        key_hits.extend(f"{context}[{i}].{h}" for h in find_forbidden_keys(rec))
        leak_hits.extend(f"{context}[{i}].{h}" for h in find_id_or_contact_leaks(rec))
    if key_hits or leak_hits:
        raise AssertionError(
            "POPIA leak in {ctx}: keys={keys} values={vals}".format(
                ctx=context, keys=key_hits[:20], vals=leak_hits[:20]
            )
        )
