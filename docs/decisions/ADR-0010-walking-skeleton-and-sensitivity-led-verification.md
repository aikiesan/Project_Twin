# ADR-0010 — Walking skeleton first; verification led by sensitivity; Phase 1 limited to cane and manure

- **Status:** Accepted
- **Date:** 2026-10-05
- **Deciders:** project lead (Lucas), with the AI-assisted review of the plan

## Context
On 2026-10-05, three days into the 30-week plan, infrastructure was ahead of schedule. The repo, CI, PostGIS with 41 tables, the viewer and a registry of 117 sources were in place. The parts of Phase 0 that set the timeline had not started:

- **Parameters:** 1 of 43 process and economics parameters was `V`, against a Gate 0 target of 60 %.
- **Requests:** no LAI request had been filed and no partner email sent.
- **Model:** the process module was empty, and no stage produced engine output.

Gate 0 asked for most parameters to be verified before any modelling, so there was no ranking of which parameters move the results. Phase 1 also held more work than one person can do in five weeks: facilities, RenovaBio extraction, Bayesian Huff, residue Monte Carlo, Sentinel-2 harvest detection and every non-cane substrate.

## Decision
1. **Walking skeleton before the full panels.** Phase 0 ends with an end-to-end chain for the two calibration mills, Costa Pinto and Narandiba: cane, then residues and manure, then monthly CH₄ (Level-1 CSTR mass balance), then LCOB (annuity). It is compared with ANP monthly output. The skeleton uses the existing parameters with their current flags.
2. **Verification led by sensitivity.** A Morris screen on the skeleton ranks the parameters. Verification starts with the top-ranked ones. Gate 0 becomes "≥ 60 % of the top-15 parameters are `V`", plus the skeleton running and LAI R1, R2 and R4 filed. The PROJECT.md success criterion (≥ 80 % `V` among parameters used in results) is unchanged.
3. **Phase 1 covers cane and manure only.** Sewage sludge, OFMSW, slaughterhouses, dairies and the Sentinel-2 harvest detection move to Phase 1b, which runs alongside Phase 2 as time allows.
4. **External requests are the critical path.** LAI requests and partner emails are filed first, before more data is imported. New imports are limited to what the next model step needs.
5. **The PILAR-2b dump restore moves to Phase 5**, the first phase that needs the `pilar2b` schema.

## Consequences
- \+ Early evidence on hypotheses H2.1 and H3.2 and on conflicts C2 and C6. Verification effort goes where it changes results.
- \+ Phase numbers stay the same, so the references in docs/05, 06, 18, 20 and PROJECT.md stay valid.
- − The skeleton's first numbers rest on `S` and `K` parameters. They are labelled as v0 and must not be published or exported to PILAR-2b.
- − Later phases shift by about three weeks (Phase 5 ends around week 33).
- **Follow-up:** docs/19 rewritten; the PROJECT.md timeline updated; docs/05 §7 points here.

## Alternatives considered
- **Keep the original order (verify, then build).** Rejected: without a sensitivity ranking, most of the verification effort would go to parameters that barely move the results, and the model would start later.
- **Keep all substrates in Phase 1.** Rejected: it does not fit five weeks for one person, and only manure is needed for the co-digestion hypothesis H2.1.
