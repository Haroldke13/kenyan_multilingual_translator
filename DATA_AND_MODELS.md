# What you may do with this, in practice

The code is Apache-2.0. The data and the models are not, and two of them are
stricter. This page is the honest version, because "it's open source now" is
true of the code and misleading about everything else.

## The short version

| | Licence | What that means for you |
| --- | --- | --- |
| **The code** — everything under `language_ai/`, `MOBILE_VERSION/mobile/`, `scripts/`, `tests/`, `ui/` | Apache-2.0 | Use it, change it, sell it, fork it. Keep `LICENSE` and `NOTICE`. |
| **Bible corpora in this repo** | CC BY-SA 4.0 + public domain | Keep attribution, and anything derived stays CC BY-SA. |
| **NLLB-200 and MMS** (downloaded, not shipped) | CC BY-NC 4.0 | **Non-commercial only.** |

So: **as it ships, you can study it, extend it and run it — but you cannot sell
a service built on it**, because the two models it downloads forbid commercial
use. That is a constraint of Meta's model licences, not of this project, and
swapping in differently-licensed models removes it.

## The code — Apache-2.0

Chosen over MIT for two reasons that matter here.

**It has an explicit patent grant.** This is machine-translation code; patents in
that area exist. Apache-2.0 grants contributors' patent rights to users and
terminates that grant for anyone who sues over them. MIT says nothing at all
about patents.

**It settles what happens to contributions.** Section 5 says that anything you
deliberately submit for inclusion is under the same licence, unless you say
otherwise in writing. That means a pull request needs no separate contributor
agreement to sign, and a contributor keeps their copyright while everyone gets
the same rights to it. Without that clause, a public repository taking pull
requests leaves everyone guessing — which is exactly the situation this change
was made to end.

## The Bible corpora — CC BY-SA 4.0, and it is contagious

These files are in the repository and are therefore being redistributed:

```
data/bible/parallel.jsonl
MOBILE_VERSION/data/*/verses.jsonl.gz
models/translation/*/parallel.*.jsonl
```

- **Kikuyu text** — Biblica's Open Kikuyu Contemporary Version, **CC BY-SA 4.0**
- **English text** — World English Bible, **public domain**
- Both from [eBible.org](https://ebible.org/)

CC BY-SA has two obligations and the second one surprises people:

1. **Attribution.** Keep the credit, including in anything you build from it.
2. **Share-alike.** A derivative work must be released under CC BY-SA 4.0 too —
   **and a model trained on this text is a derivative work.** If you fine-tune on
   `parallel.jsonl` and publish the weights, those weights are CC BY-SA.

If that does not suit you, `scripts/download_bible_data.py` takes explicit URLs,
so you can build the same corpus from a text you have your own licence to.

Corpora added for other languages should state their source and licence in the
pull request. A corpus with no known licence cannot be merged, however good it
is — see `CONTRIBUTING.md`.

## The models — CC BY-NC 4.0, non-commercial

| Model | Used for | Licence |
| --- | --- | --- |
| `facebook/nllb-200-distilled-600M` | translation | CC BY-NC 4.0 |
| `facebook/mms-1b-all` | speech recognition | CC BY-NC 4.0 |

Neither is in this repository. The app fetches them from the Hugging Face Hub on
first use, so their licences bind **you**, as the person who downloaded them,
rather than this project.

**Non-commercial means non-commercial.** Charging for access, bundling it into a
paid product, or running it as an internal tool of a commercial operation are all
outside CC BY-NC. Research, study, personal use, teaching and non-profit use are
inside it.

If you need commercial use, the code is Apache-2.0 and the model layer is
swappable — point `asr_model` and the translation model at something you are
licensed to use commercially. Nothing in the code assumes Meta's models
specifically.

## Recordings and contributed audio

Do not contribute a recording of somebody who has not agreed to be recorded and
published. This is the one rule here that cannot be fixed after the fact: a
voice in a public corpus cannot be recalled, and in most jurisdictions a voice
recording is personal data.

Contributed audio needs, in the pull request:

- confirmation that the speaker knew and agreed,
- the language and, where it matters, the dialect,
- a licence you are entitled to grant — CC BY-SA 4.0 or CC0 preferred.

## If you are unsure

Open an issue before opening a pull request. Licensing is the one part of this
project where a mistake is expensive and hard to undo, and nobody minds the
question.
