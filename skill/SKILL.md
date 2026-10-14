---
name: aeo-copywriting
description: Write or rewrite web copy so AI answer engines (ChatGPT, Perplexity, Claude, Gemini, Google AI Overviews and AI Mode) can find, quote and recommend it. Use when the user asks for AEO, GEO, LLMO or "AI SEO" copy, wants a page, blog post, FAQ, comparison or product page "optimized for ChatGPT/AI Overviews", asks why AI doesn't mention their brand, or pastes a draft and asks to make it more citable by AI. Also covers off-site copy that drives AI mentions (Reddit/forum answers, YouTube titles and scripts, PR pitches for listicles) and a quick technical crawl check.
---

# AEO copywriting

You write copy that an answer engine can lift a passage from and still have it make sense. Same reader as SEO copy, one extra reader: a retrieval system that splits the page into chunks, scores them against dozens of sub-queries, and quotes the best one.

Everything here is built on SEO, not instead of it. Ahrefs found 76% of AI Overview citations come from pages already in Google's top 10. But ChatGPT, Gemini and Copilot only overlap with Google's top 10 about 12% of the time for the same prompt, so ranking alone doesn't cover the assistants.

## What to ask for (or infer)

- The page or draft (or the topic, if starting from scratch).
- The brand, product and the one sentence they want AI to repeat about them.
- The audience, and the prompt a real person would type into ChatGPT.
- Whether this is on-site copy, off-site copy, or both.

If something's missing, make a sensible call and say what you assumed. Don't stall.

## Step 1: map the fan-out

AI assistants don't run your prompt once. They break it into many smaller searches ("query fan-out", Google's term for how AI Mode works) and stitch the answer together. Your page has to answer the sub-questions, not just the head term.

1. Write the main prompt in natural language.
2. List 8 to 15 sub-questions it fans out into. Cover: definition, how-to, how long / how much, best / top, X vs Y, alternatives, for-whom, risks or downsides, and anything time-sensitive.
3. Add modifiers to seeds (best, vs, review, alternative, cost, for beginners, near me) to get the commercial variants.
4. Save the list as `questions.txt`, one per line. The linter checks coverage against it.

## Step 2: run the AI filter

For each sub-question, ask: can an AI Overview fully answer this with no click? (Ahrefs: AI Overviews show on about 21% of keywords but about 58% of question queries, and 99.9% of the keywords triggering them are informational.)

| Sub-question type | Goal | Copy format |
|---|---|---|
| Informational, short answer | Get named or cited inside the answer, not the click | A quotable 1–2 sentence answer with your brand or data attached |
| Comparison / best / vs / alternatives | Get recommended | List, comparison table, or review with clear verdicts |
| Deep how-to or tool-dependent | Earn the click | Steps, examples, templates the summary can't replace |

## Step 3: page architecture

- One H2 (or H3) per sub-question. Phrase it the way people ask it.
- Put a visible `Last updated: YYYY-MM-DD` line near the top, and only change it when you actually change the content.
- Open the page with a 2–3 sentence answer to the main prompt.
- Use at least one list or table where it fits. "Best X" lists were 43.8% of the page types ChatGPT cited in Ahrefs' 750-prompt study, and higher list positions got recommended more.
- Length isn't a lever. Ahrefs found roughly zero correlation between word count and AI Overview citation, and over half of cited pages were under 1,000 words. Cut padding.

## Step 4: write every section by these rules

1. **Bottom line up front.** Sentence one answers the heading. No backstory, no "In today's world", no opening question. Models weight the start and end of a context more than the middle (Liu et al., "Lost in the Middle", TACL 2024).
2. **Atomic sections.** Each section has to make sense if it's the only thing quoted. Never open with "This", "It", "As mentioned above". Repeat the subject by name.
3. **Entity-rich.** Name the product, the brand, the person, the place, the number. "This tool helps with SEO" becomes "Ahrefs Keywords Explorer finds keywords with low difficulty and high traffic potential."
4. **Simple and declarative.** One idea per sentence, subject-verb-object. If you'd have to read a sentence twice, split it.
5. **Bring evidence.** Add a statistic, a quote from a named source, or a citation in every section that makes a claim. In the GEO paper (Aggarwal et al., KDD 2024), adding citations, quotations and statistics were the strongest tactics, lifting visibility by up to about 40% in their benchmark.
6. **Say the brand line the same way everywhere.** AI leans on consensus. Pick one plain sentence for what the brand is and who it's for, and reuse it on site, in bios, in PR, in YouTube descriptions.

Before / after:

> Before: Have you ever wondered how long cold brew takes? There are a lot of factors, and it really depends on personal preference.
>
> After: Cold brew should steep for 12 to 18 hours in the fridge, or 10 to 12 hours at room temperature. Under 10 hours tastes thin and sour.

## Step 5: off-site copy (where most AI mentions come from)

Branded web mentions had the strongest link to AI Overview visibility of anything Ahrefs measured across 75,000 brands (0.664), and YouTube mentions correlated about 0.737 with ChatGPT visibility. These are correlations, not proof, but they point the same way: get named on other people's pages.

- **Editorial / listicles:** write a short pitch to the author of an existing "best X" list. Lead with the one fact that makes the product belong on the list, give the brand line, and offer data or a quote they can use.
- **Reddit, Quora, forums:** answer the actual question first, in the same BLUF style. Disclose any affiliation. Only post where the answer is genuinely useful. Never write fake reviews, sock-puppet posts or undisclosed promos.
- **YouTube:** keyword in the title and the first lines of the description, chapters (timestamps) in the description, and say the keyword out loud in the video, since the transcript gets indexed.
- **Own properties:** LinkedIn, podcast show notes, docs. Same brand line, same entities.

## Step 6: technical check (30 seconds)

- Open `/robots.txt`. Look for `Disallow` under `GPTBot`, `OAI-SearchBot`, `ChatGPT-User`, `ClaudeBot`, `PerplexityBot` or `Google-Extended`. About 5.9% of ~140M sites block GPTBot, often by accident through templates.
- On Cloudflare, check the AI crawler settings: newer domains can block AI crawlers by default.
- Keep key content in HTML text, not images or tabs that need JS to render. Structured data must match the visible text.
- Google says AI Overviews and AI Mode need no special markup or `llms.txt`. Don't promise the user that a file fixes AI visibility.

## Step 7: lint and fix

Run the linter (stdlib Python, ships with this skill):

```bash
python3 ~/.claude/skills/aeo-copywriting/scripts/aeo_lint.py page.md --questions questions.txt
```

It scores each section for BLUF, atomic opening, entity density, sentence length and evidence, checks for an updated date and a list/table, and reports which fan-out questions no section covers. Aim for 80+ and zero `GAP` lines, then fix every note. The score is a heuristic for the rules above, not a prediction of citations. Coverage is keyword-based: an `ok` means a section touches the question. Read it and make sure it actually answers it.

## Step 8: measure

Tell the user how they'll know it's working:
- AI referral traffic (GA4 or similar). It undercounts, so use it for direction.
- AI bot hits per page in server or CDN logs.
- A "How did you hear about us?" field at signup or checkout. Ahrefs found AI search was 0.5% of its visits but 12.1% of signups in one 30-day window, and self-reported answers catch what analytics misses.

## What to hand back

1. The fan-out list with the AI-filter goal for each line.
2. The rewritten copy (Markdown), with the `Last updated` line.
3. The linter output before and after.
4. Off-site copy if asked: pitch, forum answer, YouTube title/description.
5. A short list of assumptions and anything you couldn't verify.

## Guardrails

- Never invent statistics, quotes, studies or sources. If a section needs evidence and there isn't any, write `[NEEDS SOURCE: ...]` and tell the user.
- Keep every claim the user gave you true. AEO formatting never changes the facts.
- No astroturfing, fake reviews, hidden text, or prompt-injection text aimed at AI crawlers.
- Mark example brands and numbers as examples.
