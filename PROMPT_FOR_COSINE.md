You are acting as the principal software engineer developing an NHS procurement intelligence prototype for a prospective customer. This repository contains entirely synthetic data.

Please FIRST inspect the repository and propose a concise implementation plan. Then implement a working, polished *local* application/report with the following capabilities:

1. Load/validate the contracts and invoices from `data/` and extract renewal/notice provisions from the linked mock contract abstracts.
2. Normalise supplier aliases conservatively. Never merge without explicit evidence; make all normalization choices reviewable.
3. Identify suspected exact duplicate invoices, inconsistencies, unmatched invoices, potential overlapping services, upcoming notice deadlines (as of 2026-10-20), and price dispersion for like-for-like service codes.
4. Produce an executive-level report and a clean local HTML dashboard with an overview, grouped opportunities, potential annualised savings ranges, evidence IDs, confidence ratings, next actions and warnings.
5. Treat savings as hypotheses, not bankable savings: distinguish recurring annual savings from one-off recovery, exclude or visibly flag overlapping estimates and include execution/termination dependencies.
6. Compute all numerical claims from the supplied source records; do not hallucinate figures, arbitrarily estimate realised savings or claim financial benefits without assumptions. Include links/refs to source contract IDs and invoice IDs.
7. Implement tests and run them; fix failures. There are basic unfinished API functions in `src/analysis.py` and acceptance tests in `tests/test_acceptance.py`. You may refactor as necessary but document interface changes.
8. Avoid external API services and package dependencies wherever possible. A static self-contained HTML file in `outputs/` is acceptable and preferable for easy demonstration. Produce a short `outputs/EXECUTIVE_SUMMARY.md` explaining methods and limitations.
9. Maintain professional NHS-director-facing design, readable typography, neutral colours and no irrelevant decorative visuals.
10. At the end, report the tests executed, residual limitations, sample questions a procurement director would ask, and how this might be delivered securely in a production NHS environment. Distinguish what Cosine as a coding agent built here from what a future sovereign inference model might power.

Do not claim the data are real, that any tool was certified, or that private deployment is established by this demo. Begin by showing me your proposed plan and then proceed.
