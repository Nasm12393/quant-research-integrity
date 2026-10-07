# Publication Checklist

Apply this checklist before any new public release or update.

## Content boundary

- Search the complete release tree for private project identifiers, local
  paths, credentials, account data, protocol thresholds, internal hashes, and
  production market values.
- Confirm that all examples and case-study facts are explicitly synthetic.
- Confirm that no client or private generated reports, caches, logs, archives,
  or environment files are included. The three allowlisted synthetic sample
  PDFs are intentional public examples and must be reviewed separately.
- Run the clean and contaminated demonstrations and retain only synthetic
  output if screenshots are prepared.

## History boundary

- Do not publish by pushing the existing private Git history.
- Export the reviewed working tree into a new release directory.
- Initialize a new Git repository from that audited tree so removed private
  text cannot survive in earlier commits.
- Review the public commit author name and no-reply email before the first
  commit.

## Technical checks

- Build a fresh candidate with `scripts/build_public_release.ps1`; the command
  must refuse an existing destination and report `PUBLIC_RELEASE_CANDIDATE_OK`.
- Run compile and tests with `PYTHONDONTWRITEBYTECODE=1`, or remove all
  generated `__pycache__` directories before the final hash and commit.
- Run `python -m compileall -q quant_integrity tests`.
- Run `python -m unittest discover -s tests -v`.
- Run both README demonstrations and verify exit codes `0` and `2`.
- Run `git diff --check` in the clean release repository.

## Human decisions

- Choose a license deliberately before publication. No license is granted by
  implication.
- Approve the public project name, author identity, contact route, and service
  wording.
- Obtain a final human privacy and methodology review before creating a public
  remote.
