# aeo_lint.py

Scores a Markdown page on how easy it is for an answer engine to quote. Standard library only, Python 3.8+.

```bash
python3 code/aeo_lint.py code/samples/before.md --questions code/samples/questions.txt --today 2026-10-14
python3 code/aeo_lint.py code/samples/after.md --questions code/samples/questions.txt --today 2026-10-14
python3 code/aeo_lint.py your-page.md --json
```

- `--questions`: a text file with one fan-out sub-question per line. Optional.
- `--today`: pin the date so the freshness check is reproducible. Defaults to today.
- `--json`: machine-readable output.

Each H2/H3 is one chunk. Per chunk it scores:

| Check | What it looks for | Weight |
|---|---|---|
| bluf | sentence 1 isn't a question, a backstory opener, or over 30 words | 25 |
| atomic | sentence 1 doesn't start with "This", "It", "As mentioned"; no "see above" | 15 |
| entities | named things + numbers per 100 words (target 6); vague phrases cost points | 20 |
| simple | share of sentences over 25 words, average length | 20 |
| evidence | stats with units, quotes, citations (target 2 per section) | 20 |

Page score = 85% word-weighted section average + 5 for a fresh `Last updated` date + 5 for a list or table + 5 for fan-out coverage.

The samples are an example page for a fictional brand (Northbean). Their coffee numbers are there to exercise the linter, not as sourced claims.

Limits: it's regex heuristics. It can't tell a true stat from a made-up one, and fan-out coverage is keyword overlap (it ignores seed words shared by most questions), so it shows that a section touches a question, not that it answers it.
