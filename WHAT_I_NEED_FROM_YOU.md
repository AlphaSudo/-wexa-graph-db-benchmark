# What I Still Need From Ahmed

Local implementation and controlled-database setup are complete. GCP and paid services are not
required. Do not send any credential through chat or commit it to this repository.

## Required before the two managed official runs

1. Rotate the CognoDB password that appeared in the conversation, while keeping the current free
   c0 instance if recreating it would risk the zero-cost constraint.
2. Confirm whether the Neo4j instance is **AuraDB Free** or a Professional 14-day trial. The
   official comparison must use AuraDB Free.
3. Rotate the Aura password that appeared in the screenshot.
4. Create `C:\Java Developer\wexa\.env` from `.env.example` and place only the replacement values
   there:

   ```text
   COGNODB_URI=
   COGNODB_USERNAME=
   COGNODB_PASSWORD=
   AURA_URI=
   AURA_USERNAME=
   AURA_PASSWORD=
   ```

5. Save sanitized screenshots showing the CognoDB c0 tier/region/limits and the AuraDB Free
   tier/region. Do not display either password.

The existing CognoDB `us-east4` region can be used and disclosed. Exact managed-region parity is
not required by the assessment, and neither managed result will be presented as hardware-equal to
the local controlled engines.

## Required before publication/submission

- Choose the article location: LinkedIn article, Dev.to, Hashnode, or a personal site.
- Decide whether you will record the prepared 60-90 second walkthrough.
- Review the final README/article claims against the generated report.
- Send the final email yourself to `hr@wexa.ai` with subject
  `CognoDB Assignment 1 – Ahmed Yasser Morra` before 2026-08-26 10:03 Africa/Cairo.
- Rotate/revoke benchmark credentials after the final managed runs.

## Already resolved

- Candidate and deadline details are recorded.
- Public repository and six-target matrix are approved.
- Budget is zero; GCP is not used.
- MovieLens data, four local engines, resource caps, correctness gates, evidence capture, reporting,
  and audit automation are implemented.
- The repository's leading hyphen is awkward but does not block submission.
