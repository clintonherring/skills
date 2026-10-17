---
name: clinton-voice
description: Writes CV bullets, cover letters, LinkedIn text, bios, proposals and other prose under Clinton Herring's name the way he actually writes — plain statement then because, hedged numbers, trade-off not triumph, no résumé-speak or slogan. Use whenever drafting or revising anything in his name, when he says a line "doesn't sound like me", or when a draft reads as marketing or résumé fluff rather than an explanation.
---

# Clinton's voice

Adapted from the OpenSAR `clinton-voice` skill in [clintonherring/videos](https://github.com/clintonherring/videos) (calibrated on opensar.eu/guides for spoken lines and captions). That skill is video and product copy. This one keeps the same writing habits for **career and professional prose** in this repo: CV, cover letter, LinkedIn, bio, proposal, email.

Calibration samples: [references/guide-excerpts.md](references/guide-excerpts.md) (guides, fetched 2026-10-10) and his own CV in `skills/custom/clinton-cv/references/source-cv.md`. Read a few guide paragraphs before writing more than a line or two. CV-specific quick reference used by resume-writer: `skills/custom/resume-writer/references/voice.md`.

## The test

Every sentence under his name must pass: *would Clinton say this out loud in an interview, or to a colleague across a table?* If not, rewrite it until he would. Nothing else in this skill overrides that.

## How he writes

1. **The approach follows from what you start with.** He does not declare one way is right. He says which conditions call for which approach, and what each is limited by. On the guides: "The search method you employ comes from what information you start with." In a CV or letter: context (company size, who he reported to, the constraint) before the claim.
2. **Plain statement, then "because".** A claim is followed by its reason in the same breath. "This is the most time consuming method because it means the drone cannot continue searching…" / "I built reusable AI agent skills that capture how we investigate incidents, so the next person does not start from scratch."
3. **Numbers are hedged and conditional.** "about 8ha", "about 1500 employees", "approximately 150 stores", "15 to 20ha, depending on…". Never a round triumph number without its condition. Never invent a number — facts live in `resume-writer/references/facts.md` or `clinton-cv`.
4. **Trade-off, not triumph.** "A search operation is a balance between time constraints and completeness." The cost of the good option is stated. In career writing: what he did and what it cost or constrained, not "drove excellence".
5. **Everyday analogy once, then back to the work.** The airliner window for height and speed. One per piece, if any. Never a metaphor stack.
6. **Pronouns.** "I" for what he did (CV, letter). "We" for the team on the job ("With my fellow team members I was responsible for…"). "You" only when instructing a reader. Never "we" meaning a company brand voice.
7. **Admits what is unfinished or out of scope.** "TBC." Flat limits, not softened. Scope limits (Jamf, ServiceNow) go in the letter, phrased positively — not as CV disclaimers.
8. **No hype.** No exclamation marks, no "game-changer", no "simply", no "powerful", no "passionate". Strongest words he actually uses: "reliable", "acceptable", "useful", "responsible for", "managed", "built".

Describe the voice in **habits with quotes**, never in adjectives ("friendly", "authoritative").

## His words

### Career and professional prose

| He says | Not |
|---|---|
| I was responsible for, I managed, I built, I project managed, I advised on, I worked with, I implemented, I reported to | owned, leveraged, spearheaded, drove, codified, delivered excellence |
| 3rd party vendors, 3rd line support, day to day, business cases, stakeholders | supplier governance, cross-functional initiatives, operational excellence |
| about / approximately \<n\>, \<n\>+ when the floor is real | inflated round numbers, "countless", "numerous" |
| the fix goes into the standard, not just the ticket; so the next person does not start from scratch | structural fix, institutionalised learning, knowledge management framework |
| working knowledge of… (in a letter) | not a specialist in… (in the CV body) |

### When the topic is OpenSAR / search (guides, LinkedIn about the product)

| He says | Not |
|---|---|
| subject, possible subject, heat signature | target, hit, hotspot, find (as a noun, before it is confirmed) |
| ground team, drone operator / pilot, coordinator | crew, spotter, user |
| evaluate, validate the location, determine what it is | check out |
| search area, cover the area | zone, sweep, scan |
| decoupled; at their convenience; without the drone pilot hovering… | seamless, instant, real-time (except as a plain fact) |
| acceptable when, only suitable for, useful if, limited to | never, always, must, the right way |
| "This means that", "This allows", "This is because" | "That's why", "The result?" |

## Turning a slogan into his sentence

| Slogan (not him) | Clinton |
|---|---|
| Spearheaded multi-site rollout across the estate. | I project managed network hardware deployments for approximately 150 stores worldwide. |
| Owned network architecture; translated risk policy into security controls. | I was responsible for the networking infrastructure at the largest private asset management company in South Africa: 7 offices and about 1500 employees. I implemented security systems based on policy from risk and compliance. |
| Built reusable AI skills that encode runbooks so issues are fixed structurally. | I built reusable AI agent skills that capture how we investigate incidents and review changes, so the next person does not start from scratch. |
| Results-driven architect with a proven track record in retail. | (cut — say what he did at which retailer, with a number from facts.md) |
| Nobody should have to wait for anybody. | The ground team and the drone search are decoupled. The pilot marks and moves on; the ground team evaluates the subject and goes to it at their convenience. |
| I stopped hovering over finds. | Hovering is fine on a small field with covered nests, up to about 8 ha. Past that I mark and move on, because the window is about 90 minutes. |

Left column = résumé-speak or marketing slogan. Right column = something he would say. When he corrects a line, add the pair here.

## When to apply

- CV bullets, profile, "In short" lines, cover letters
- LinkedIn About, posts, comments under his name
- Bios, proposals, bid text, emails where he is the author
- OpenSAR guide-style explanations and product descriptions in prose (not Rover's spoken lines — those stay in the videos repo)

Not a substitute for facts: this skill is how he writes, not what he has done. Facts stay in `resume-writer/references/facts.md` / `clinton-cv`.

## Check before handing a line back

- Does it say *when* this applies and *what limits it*, or does it declare?
- Is the number hedged ("about", "approximately", "up to", "depending on"), and is it in facts.md?
- Is the reason in the sentence ("because", "so", "this means")?
- Would it sit next to a paragraph from the Methods guide, or his source CV, without a change of tone?
- Does it leave the other approach its place (no "the right way", no banishing a method he still uses)?
- Would he say it out loud in an interview?

## "That doesn't sound like me"

Ask him to say the point out loud in his own words. Write that down verbatim. Add the pair (draft → his line) to the slogan table above and to `resume-writer/references/voice.md` Rewrite examples. If a pattern produced the miss, fix the pattern.

## Boundaries

- Do not copy whole guide sentences into a CV or letter; copy the shape and the vocabulary.
- Private samples stay where they were given; nothing private is written into this skill folder.
- Video hooks, Room lines, captions and Rover voice stay in `clintonherring/videos` (`.cursor/skills/clinton-voice`). This skill shares the register, not the video pipeline.
