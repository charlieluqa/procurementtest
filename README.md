# NHS Procurement Intelligence — Cosine Interview Demo

**ALL DATA FICTIONAL.** Created specifically as a developer-agent exercise. None of the trusts, suppliers, invoices or contracts represent real organisations or spending.

## Goal
Use Cosine as an AI **software engineering agent** to transform inconsistent structured data and 49 mock contract abstracts into an auditable procurement intelligence product.

This is an agent-building demonstration, **not** evidence of clinical or finance-model accuracy, verified NHS savings, private hosting or the capabilities of an unreleased Lumen Sovereign model.

## Why this is a good Cosine test
- The agent must read an unfamiliar repository, inspect CSV and document files, write reusable analysis code, add tests and deliver an inspectable report.
- Results require provenance back to exact contract IDs / invoice IDs; unsupported confident assertions count as failure.
- There are supplier aliases, anomalous prices, suspected duplicate invoices, upcoming renewal windows, overlapping services and unmapped invoices.
- *Potential* savings must be explicitly distinguished from realised or cash-releasing savings, and cannot be double-counted.

## Run
1. Extract this folder and open the folder as a project in Cosine Desktop, or put it in your own private Git repository and connect Cosine Cloud. Use **synthetic data only**.
2. Select **Lumen Outpost** in the model picker if you want to evaluate a Cosine-trained model. Cosine supports other models too: verify what is selected before making claims.
3. Paste `PROMPT_FOR_COSINE.md` as the task.
4. Observe its plan, code diffs, tests and generated output. Run `python -m unittest discover -s tests -v` to verify.
5. During any interview, say *this is a synthetic coding-agent prototype*, not a live NHS system or an LLM deployed in a sovereign environment.

## Expected files
- `data/contracts.csv`: 49 fake procurement contracts
- `data/invoices.csv`: synthetic January–June invoices with deliberate anomalies
- `data/contracts/*.txt`: concise mock contract abstracts
- `src/analysis.py`: deliberately unfinished implementation
- `tests/test_acceptance.py`: deliberately failing tests until implemented
- `PROMPT_FOR_COSINE.md`: copyable instruction for Cosine

## Gold-standard discussion points
- Is this a buyer's actual pain, or just an attractive demo?
- How would the product ingest raw contracts, scanned PDFs and ERP feeds in practice?
- How do we prove ROI beyond finding accounting anomalies?
- Would Cosine sell the software agent directly, or license models/agents to existing vendors?
- What is the security, deployment and assurance case for processing sensitive procurement data?
