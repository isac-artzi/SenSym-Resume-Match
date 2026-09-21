# Extending SenSym Resume Match

This app is a teaching artifact as much as a tool — every module is short
enough to read in one sitting, and the ideas below are starting points, not
a roadmap anyone owns. Pick one, read the module it touches, and go. Pull
requests welcome.

A few things worth knowing before you start:

- **Prompts are plain text**, in `prompts/`. You can change how the app
  writes without touching a line of Python.
- **The LLM client is two functions**: `complete()` and `complete_json()` in
  `resume_match/llm.py`. Any new provider-specific behavior goes there;
  everything else in the app should stay provider-agnostic.
- **The no-invention rule is the whole point of this app.** If your change
  touches `prompts/bundle.txt`, `prompts/profile.txt`, or
  `resume_match/pipeline.py`, make sure the fidelity check still runs
  against whatever you generate, and test it with a credential profile that
  has real gaps.

## Ideas, roughly easiest to hardest

**Multilingual output, with a back-translation fidelity check** — *touches
`prompts/`, `resume_match/pipeline.py` · easy-medium.* Add a target-language
preference, translate the bundle prompt's output instructions, and
back-translate the result before the fidelity check so invented content
can't hide behind a language switch.

**Accessibility pass on the generated DOCX** — *touches `resume_match/render.py`
· easy.* Add a dyslexia-friendly font/spacing option and confirm the
generated documents work well with screen readers (heading structure,
alt text where relevant, reading order).

**Fine-grained evidence footnotes** — *touches `prompts/bundle.txt`,
`resume_match/render.py` · easy-medium.* Every profile item already carries
an `evidence` field pointing at its source file. Thread that through to the
generated resume bullets and render it as a footnote or endnote in the
DOCX, so every claim is one click from its source.

**"Resume A/B" mode** — *touches `prompts/bundle.txt`,
`resume_match/pipeline.py`, `app.py` · medium.* Generate two tailored
resumes for the same job with different emphases (e.g. leadership vs.
technical depth) and let the student compare them side by side in Review.

**Study plan compiler** — *touches `resume_match/pipeline.py`,
`resume_match/render.py` · medium.* Take the gap analysis's suggestions and
turn them into a dated, week-by-week plan, exported as an `.ics` calendar
file the student can import.

**Portfolio site generator** — *new module, reads `resume_match/pipeline.py`'s
profile output · medium.* Render the credential profile as a static personal
website (a single HTML file with inline CSS would fit this repo's spirit).

**Skills-graph view** — *new module, likely a small Streamlit component ·
medium-hard.* Plot the student's skills against the job's requirements as a
radar or network graph, and animate the gap closing as the student marks
planned activities as done.

**A "recruiter's eye" critique agent** — *touches `resume_match/pipeline.py`,
a new prompt file · medium.* A second-pass prompt that reads the finished
resume the way a screener would in the first seven seconds and reports what
actually stands out (or doesn't).

**Mock-interview mode** — *touches `resume_match/pipeline.py`, `app.py`,
possibly `resume_match/llm.py` for voice · hard.* A chat (or voice) loop that
asks the interview-prep questions one at a time and scores the student's
answers against their own credential profile — the no-invention rule applies
to the scoring too, not just the documents.

**Local-only mode with prompt engineering for small models** — *touches
`prompts/`, `resume_match/llm.py` · hard.* Get the whole pipeline working
end to end on a small Ollama model (7B-class). The interesting problem is
prompt engineering: small models are more prone to inventing details, so
this is really about making the no-invention rule hold under a weaker model.

**Batch evaluation harness** — *new module or `scripts/` directory · hard.*
A set of synthetic student profiles and job postings, run through the
pipeline automatically, with a hallucination scorer that flags invented
claims without a human reading every output. This is what would let prompt
changes be measured instead of eyeballed — genuinely useful before merging
any change to `prompts/bundle.txt`.

**Integration experiments** — *touches `resume_match/ingest.py` for
fetching, `resume_match/render.py` for output · varies.* Pull job postings
from an RSS feed or an ATS API instead of saved files, or push the finished
bundle to a Google Drive folder the student owns instead of downloading a
ZIP. Each of these is its own small project; start with read-only fetching
before attempting to write anywhere.

## Shipped since the demo build

Two things originally deferred to v1.1 are now in `main`: Google Drive
folder input (`resume_match/drive.py`, wired into the Materials and Jobs
sections of `app.py`) and a pre-generation cost estimate
(`resume_match/cost.py`, shown near the Generate button). Both are good
examples if you want to see the "optional convenience, upload/no-estimate
still works fine without it" pattern this app leans on — Drive fetch
failures fall back to a friendly message rather than blocking anything, and
the cost estimate is explicitly labeled approximate rather than treated as
a real bill.

If you touch either: `resume_match/cost.py`'s per-job token constants
(`BASE_INPUT_TOKENS_PER_JOB`, `BASE_OUTPUT_TOKENS_PER_JOB`) were derived
from a handful of real runs against Claude Sonnet 5 with extended thinking
disabled — if you change what the bundle prompt asks for, or the provider
pricing in `PROVIDER_PRICING` goes stale, re-derive both from a real run
rather than guessing.

Both are good first contributions: scoped, don't touch the pipeline's
correctness, and have a clear "done" state.
