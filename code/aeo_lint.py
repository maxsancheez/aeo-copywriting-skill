#!/usr/bin/env python3
"""aeo_lint.py: score a Markdown page for how easy it is for an answer engine to quote.

Each H2/H3 section is treated as one "chunk" (AI retrieval cuts pages into passages,
so every section should survive on its own). Checks per section:

  bluf      first sentence gives the answer, not backstory or a question
  atomic    first sentence doesn't lean on earlier text ("This", "As mentioned")
  entities  named things and numbers per 100 words; vague phrases cost points
  simple    short, declarative sentences (one idea each)
  evidence  stats, quotes and citations (strongest lever in the GEO paper)

Page checks: a visible updated date, list/table formats, and (optional) coverage
of fan-out sub-questions you pass with --questions.

Standard library only. Usage:
  python3 aeo_lint.py page.md
  python3 aeo_lint.py page.md --questions questions.txt
  python3 aeo_lint.py page.md --json
"""
import argparse
import datetime as dt
import json
import re
import sys

# ---- dials (illustrative weights, see README "Assumptions") ----------------
WEIGHTS = {"bluf": 25, "atomic": 15, "entities": 20, "simple": 20, "evidence": 20}
LONG_SENTENCE = 25          # words; above this a sentence counts as "long"
TARGET_ENTITY_DENSITY = 6.0  # named things + numbers per 100 words for full marks
TARGET_EVIDENCE = 2          # stats/quotes/citations per section for full marks
FRESH_DAYS = 365             # "updated" date older than this is flagged
COVER_THRESHOLD = 0.6        # share of a question's content words a section must contain

BACKSTORY_OPENERS = re.compile(
    r"^(in today'?s|when it comes to|before we|have you ever|let'?s (talk|dive|start)|"
    r"in this (article|post|guide|section)|we('ll| will) (look|explore|cover)|"
    r"there are (many|a lot of|several)|it'?s no secret|imagine|ever wondered|"
    r"as you (may|might) know|first,? let'?s)",
    re.I,
)
BACKREF_OPENERS = re.compile(
    r"^(this|that|these|those|it|they|as (mentioned|noted|we saw|discussed)|"
    r"like we said|also|another|furthermore|additionally|however|but|and)\b",
    re.I,
)
VAGUE = re.compile(
    r"\b(this tool|our (tool|product|solution|platform)|the solution|the product|"
    r"many experts|some people|a lot of|lots of|various|numerous|"
    r"best-in-class|cutting-edge|game[- ]changer|world-class|state-of-the-art)\b",
    re.I,
)
STOP = set(
    "a an the and or but of to in on for with by at from is are was were be been it its "
    "this that these those how what which who why when where do does did can should i you "
    "your my we our they their vs versus best top".split()
)


def split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[\"'(A-Z0-9])", text)
    return [p.strip() for p in parts if p.strip()]


def words(text):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-.%$]*", text)


def strip_md(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*\|[-:| ]+\|\s*$", " ", text, flags=re.M)
    text = re.sub(r"^\s*\|(.*)\|\s*$", lambda m: m.group(1).replace("|", ",") + ".", text, flags=re.M)
    text = re.sub(r"[*_`>#]", "", text)
    return text


def parse_sections(md):
    """Split on ## / ### headings. Text before the first heading is the intro."""
    sections, title, buf = [], "(intro)", []
    for line in md.splitlines():
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            if buf and "".join(buf).strip():
                sections.append((title, "\n".join(buf)))
            title, buf = m.group(2).strip(), []
            if m.group(1) == "#":
                title = "(intro)"
        else:
            buf.append(line)
    if buf and "".join(buf).strip():
        sections.append((title, "\n".join(buf)))
    return sections


def count_entities(sentences):
    """Capitalized tokens that aren't sentence-initial, plus numbers."""
    n = 0
    for s in sentences:
        toks = words(s)
        for i, t in enumerate(toks):
            if re.match(r"^\$?\d", t):
                n += 1
            elif i > 0 and t[0].isupper() and t.lower() not in STOP and t != "I":
                n += 1
    return n


def count_evidence(raw):
    stats = len(re.findall(r"\b\d+(?:[.,]\d+)?\s?(?:%|percent|x\b|times|hours|days|minutes|ml|g\b|kg|\$)", raw, re.I))
    stats += len(re.findall(r"\$\d", raw))
    quotes = len(re.findall(r"[\"“][^\"”]{12,}[\"”]", raw))
    cites = len(re.findall(r"\]\(https?://|\[\d+\]|\(\w[\w .&]+,? \d{4}\)", raw))
    return stats + quotes + cites, {"stats": stats, "quotes": quotes, "citations": cites}


def score_section(title, raw):
    text = strip_md(raw)
    sents = split_sentences(text)
    n_words = len(words(text))
    notes = []
    if not sents or n_words < 15:
        return None

    first = sents[0]
    # BLUF
    bluf = 1.0
    if first.endswith("?"):
        bluf, _ = 0.2, notes.append("opens with a question; answer it in sentence 1")
    elif BACKSTORY_OPENERS.match(first):
        bluf, _ = 0.2, notes.append(f'backstory opener: "{first[:50]}..."')
    elif len(words(first)) > 30:
        bluf, _ = 0.6, notes.append("first sentence is long; lead with the answer in <25 words")

    # Atomic
    atomic = 1.0
    if BACKREF_OPENERS.match(first):
        atomic, _ = 0.3, notes.append(f'starts with a back-reference ("{first.split()[0]}"); name the subject')
    refs = len(re.findall(r"\b(as (mentioned|noted|discussed) (above|earlier|before)|see above|the above|below)\b", text, re.I))
    if refs:
        atomic = max(0.0, atomic - 0.3 * refs)
        notes.append(f"{refs} pointer(s) to other sections; restate instead")

    # Entities
    ents = count_entities(sents)
    density = 100.0 * ents / max(n_words, 1)
    vague = VAGUE.findall(text)
    entities = min(1.0, density / TARGET_ENTITY_DENSITY) - 0.15 * len(vague)
    entities = max(0.0, entities)
    if vague:
        notes.append("vague phrases: " + ", ".join(sorted({v if isinstance(v, str) else v[0] for v in vague})))
    if density < TARGET_ENTITY_DENSITY / 2:
        notes.append(f"low entity density ({density:.1f}/100 words); name products, people, places, numbers")

    # Simple
    lens = [len(words(s)) for s in sents]
    long_share = sum(1 for L in lens if L > LONG_SENTENCE) / len(lens)
    avg = sum(lens) / len(lens)
    simple = max(0.0, 1.0 - long_share * 1.5 - max(0, avg - 18) * 0.03)
    if long_share > 0.2:
        notes.append(f"{long_share:.0%} of sentences are over {LONG_SENTENCE} words")

    # Evidence
    ev, ev_detail = count_evidence(raw)
    evidence = min(1.0, ev / TARGET_EVIDENCE)
    if ev == 0:
        notes.append("no stat, quote or citation; add one")

    parts = {"bluf": bluf, "atomic": atomic, "entities": entities, "simple": simple, "evidence": evidence}
    score = sum(WEIGHTS[k] * v for k, v in parts.items())
    return {
        "section": title,
        "words": n_words,
        "score": round(score),
        "parts": {k: round(v, 2) for k, v in parts.items()},
        "avg_sentence_words": round(avg, 1),
        "entity_density": round(density, 1),
        "evidence": ev_detail,
        "notes": notes,
        "_text": (title + ". " + text).lower(),
        "_head": title.lower(),
    }


def page_checks(md, today):
    out = {}
    m = re.search(r"(updated|last updated|published)[^\n]{0,20}?(\d{4}-\d{2}-\d{2})", md, re.I)
    if m:
        d = dt.date.fromisoformat(m.group(2))
        age = (today - d).days
        out["updated"] = {"date": m.group(2), "age_days": age, "fresh": age <= FRESH_DAYS}
    else:
        out["updated"] = {"date": None, "fresh": False}
    out["has_list"] = bool(re.search(r"^\s*([-*+]|\d+\.)\s+", md, re.M))
    out["has_table"] = bool(re.search(r"^\s*\|.*\|\s*$", md, re.M))
    return out


def content_words(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2]


def fanout_coverage(results, questions):
    # Words shared by most questions are the seed topic ("cold brew"); every section
    # has them, so they don't tell you whether the specific sub-question is answered.
    df = {}
    for q in questions:
        for w in set(content_words(q)):
            df[w] = df.get(w, 0) + 1
    seed = {w for w, n in df.items() if len(questions) >= 3 and n / len(questions) >= 0.5}
    rows = []
    for q in questions:
        cw = [w for w in content_words(q) if w not in seed] or content_words(q)
        best, best_rank, best_sec = 0.0, -1.0, None
        for r in results:
            n = max(len(cw), 1)
            hit = sum(1 for w in cw if w in r["_text"]) / n
            rank = hit + 0.5 * sum(1 for w in cw if w in r["_head"]) / n
            if rank > best_rank:
                best, best_rank, best_sec = hit, rank, r["section"]
        rows.append({"question": q, "covered": best >= COVER_THRESHOLD,
                     "best_section": best_sec, "match": round(best, 2)})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    ap.add_argument("--questions", help="text file, one fan-out sub-question per line")
    ap.add_argument("--today", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    md = open(a.page, encoding="utf-8").read()
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    results = [r for r in (score_section(t, b) for t, b in parse_sections(md)) if r]
    page = page_checks(md, today)
    cov = None
    if a.questions:
        qs = [l.strip() for l in open(a.questions, encoding="utf-8") if l.strip()]
        cov = fanout_coverage(results, qs)

    total_words = sum(r["words"] for r in results) or 1
    section_avg = sum(r["score"] * r["words"] for r in results) / total_words
    page_score = section_avg * 0.85
    page_score += 5 if page["updated"]["fresh"] else 0
    page_score += 5 if (page["has_list"] or page["has_table"]) else 0
    if cov:
        page_score += 5 * sum(c["covered"] for c in cov) / len(cov)
    else:
        page_score += 5 * section_avg / 100
    page_score = round(min(100, page_score))

    if a.json:
        for r in results:
            r.pop("_text")
            r.pop("_head")
        print(json.dumps({"page_score": page_score, "page": page, "sections": results, "fanout": cov}, indent=2))
        return

    print(f"AEO score: {page_score}/100   ({a.page})")
    up = page["updated"]
    print(f"  updated date: {up['date'] or 'missing'}" + (f" ({up['age_days']} days old)" if up.get("date") else "")
          + ("" if up["fresh"] else "  <- add or refresh a visible 'Updated' date"))
    print(f"  list/table:   {'yes' if page['has_list'] or page['has_table'] else 'no  <- add a list, table or comparison'}")
    print()
    print(f"  {'section':34} {'score':>5} {'bluf':>5} {'atom':>5} {'ent':>5} {'simp':>5} {'evid':>5}")
    for r in results:
        p = r["parts"]
        print(f"  {r['section'][:34]:34} {r['score']:>5} {p['bluf']:>5} {p['atomic']:>5} "
              f"{p['entities']:>5} {p['simple']:>5} {p['evidence']:>5}")
    print()
    for r in results:
        for n in r["notes"]:
            print(f"  - [{r['section'][:28]}] {n}")
    if cov:
        print()
        hit = sum(c["covered"] for c in cov)
        print(f"  fan-out coverage: {hit}/{len(cov)} sub-questions answered")
        for c in cov:
            mark = "ok " if c["covered"] else "GAP"
            where = f"-> {c['best_section']}" if c["covered"] else f"(best match {c['match']:.0%})"
            print(f"    {mark} {c['question']}  {where}")


if __name__ == "__main__":
    sys.exit(main())
