# Matching a job posting to the person's facts

Working files for one application live in `<data_dir>/applications/<yyyy-mm>-<company>-<role-slug>/`: `jd.md`, `match.md`, `cv.md`, `cv-review.md`, and `cover-letter.md` if asked. Documents (`cv.docx`, `cv.pdf`) are produced only on request.

## Steps

1. **Save the posting.** Paste it verbatim into `jd.md` with the company, role title, contact name, location and on-site expectation, and the URL or date.
2. **Keyword scan.** `python3 scripts/jd_match.py jd.md`. It prints posting terms that appear in `facts.md` (MAPPED), posting terms that look like skills or tools but do not (GAPS), and facts terms the posting never mentions (UNUSED; do not pad with these). It harvests the person's own skill terms from `facts.md`, so it adapts to any profession. A hint, not the decision.
3. **Write `match.md`** from `templates/match.template.md`. Fill *Problems this employer needs solved* first, from reading the posting, before touching keywords or bullets.
4. **Choose emphasis.** Pick the two or three themes that lead; everything else supports. Record the choice and why. Name the single skill the posting leans on most and which fact proves it; that becomes the first bullet of the current role.
5. **Brain-dump check.** For each role the CV will lead with, confirm `facts.md` has result / what they did / how and at least one outcome number. If not, ask the person now, using the "Open metric questions" list; write answers into `facts.md`.
6. **Draft bullets** from the brain dumps, in their voice (`voice.md`), XYZ where a verified number exists. One idea per bullet, ≤ ~30 words.
7. **Honesty pass.** Delete any claim not in `facts.md`. Move scope limits (tools they know of but have not administered, certifications they lack) to the letter, phrased positively.
8. **Save** `cv.md` in the structure of `templates/cv.template.md`.
9. **Self-review.** `python3 scripts/cv_check.py cv.md --jd jd.md`, then score with `scorecard.md` into `cv-review.md`; iterate to threshold.
10. **Show the person** the draft with the review and the open questions. They confirm before sending.
11. **Only if asked for a document:** `python3 scripts/md_to_cvjson.py cv.md cv.json && node scripts/build-cv.js cv.json cv.docx --pdf`; check 2 pages, selectable text, < 2.5 MB.

## Reusable evidence by theme

Build this table once per person during onboarding (bottom of `facts.md`, "Proof points") and refresh it when facts change. It maps the themes postings ask for to the strongest evidence the person has, so step 4 is quick. Typical themes: leadership of people, supplier or vendor management, problem solving or root cause, delivery at scale, tools the industry uses, compliance or security, change or transformation, customer outcomes, AI or automation, language and work-status fit.

## Worked example

`examples/jd.md` → `examples/match.md` → `examples/cv.md` → `examples/cv-review.md` in the repository show the whole chain for a fictional service-delivery role.
