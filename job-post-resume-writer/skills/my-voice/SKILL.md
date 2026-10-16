---
name: my-voice
description: Builds and maintains a voice profile (voice.md) from samples of a person's own writing — URLs, documents or pasted text — and then applies it so that anything written for them (CV bullets, cover letters, LinkedIn posts, emails, proposals) reads like they wrote it. Use when the user says "build my voice", "this does not sound like me", "write this in my voice", asks to add writing samples, or when the job-post-resume-writer skill hands over after facts setup.
---

# My voice

A portable voice profile. Other skills read `voice.md` by path; this skill builds it, keeps it current, and applies it.

## Where things are

- `voice.md` lives in the data folder named in `~/.job-post-resume-writer/config.json` (`data_dir`). If there is no config, ask where the file should live, or (Claude Desktop) work with a pasted copy.
- Template: [templates/voice.template.md](templates/voice.template.md). The first line `STATUS: TEMPLATE` means the profile has not been built yet.
- Scripts (optional helpers, stdlib Python 3): `scripts/extract_text.py <file-or-url>` for samples in `.docx`, `.pdf`, `.html` or at a URL; `scripts/voice_profile.py <sample> [<sample> …]` for a quick statistical read.

## The test

Every sentence written in the person's name must pass: *would they say this out loud in an interview, or to a colleague?* If not, rewrite it until it would.

## Mode 1 — Build the profile

1. **Collect samples.** Ask for three or more pieces of writing that are theirs and unedited by others: emails they are proud of, a LinkedIn post or article, the profile text of an old CV, a project write-up, chat messages to a colleague, a proposal. Accept URLs, file paths, or pasted text. For a URL or file run `python3 scripts/extract_text.py <source>`; if it exits non-zero, ask them to paste the text. Skip anything written by a company or a copywriter for them.
2. **Read every sample in full.** Note sentence length, first or third person, the verbs they reach for, how they introduce numbers and names, how they explain a reason, what they never do (exclamation marks, buzzwords, hedging).
3. **Run the profiler** on all samples at once: `python3 scripts/voice_profile.py sample1.txt sample2.txt …`. It reports average sentence length, first-person ratio, most common verbs, recurring two- and three-word phrases, hedging words, and résumé-speak that appears in their own text. Use the output to confirm or correct what you read; do not paste it into `voice.md`.
4. **Write `voice.md`** following the template: patterns to copy with a quoted example for each; their phrases (verbatim, from the samples); words and shapes to avoid (keep the generic résumé-speak list unless they actually use a word themselves); three rewrite examples built from their real work; two XYZ sentences in their voice; the letter voice.
5. **Show it and correct it in chat.** Read it back section by section. Ask: "Is this how you talk? What is wrong?" Apply corrections. Ask them to pick the rewrite column they prefer in each example; if they prefer the left column, your reading of their voice is wrong — go back to the samples.
6. **Remove the `STATUS: TEMPLATE` line** and save. Tell the user how to add samples later ("add a writing sample").

## Mode 2 — Apply the voice

When writing anything for them:

- Read `voice.md` first, every time.
- Draft, then run each sentence against "Patterns to copy" and "Words and shapes to avoid". Replace any word from the avoid list; break noun fragments into sentences; put the verb they would use.
- Keep their phrases where they fit; never add phrases that are not in the profile or the samples.
- If the person says "this does not sound like me", ask them to say the point out loud in their own words, write that down verbatim, and add the pair to "Rewrite examples" so the profile improves.

## Mode 3 — Add a sample / update

"add a writing sample", "update my voice": extract the new sample, re-run the profiler on all samples, and amend the profile — add phrases, adjust patterns, append rewrite examples. Never remove a correction the user made earlier without asking.

## Boundaries

- The profile records how they write, not what they have done. Facts belong in `facts.md` (job-post-resume-writer skill) or whatever fact source the project uses.
- Do not copy whole sentences from samples into new documents; copy the shape and the vocabulary.
- Private samples stay in the data folder; nothing from them is written into this skill folder.
