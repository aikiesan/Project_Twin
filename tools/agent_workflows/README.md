# Claude Code agent workflows used to build this project

Scripts for the Claude Code **Workflow** tool, which runs multi-agent orchestration:
- `engine-v0-build.js` builds 7 modules, each followed by an adversarial review.
- `engine-research-sweep-2026q4.js` runs research tracks R07–R10, each with claim verification.
- `four-month-plan.js` runs a judge panel over 3 plan drafts, then a synthesis and a completeness critic.

To reuse one:
1. Edit `const ROOT = ...` at the top so it points to your local `sp-biomethane-engine` folder.
2. Ask Claude Code to run the workflow from that script path.

On 2026-10-04 these agents failed because of the usage limit, and they are the next ones to re-run:
- the build agents for renovabio (tests), economics, process, supply, siting and calibrate-anp;
- the registry-export review;
- the R07/R08 verification passes;
- the plan's third draft and its synthesis.
