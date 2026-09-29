# ChatGPT and Codex: project handoff

## Recommended division

Stay with the present evidence review until the returned Stage 1B acquisition has been qualified. Use repository-connected Codex when implementing the reference pipeline in Stage 2 and the package/tests/interface in later explicitly authorized stages. Codex can also help now with repository repairs or workflow edits; there is no scientific reason it must wait until Stage 3. ChatGPT can remain the place to review experimental design, literature, interpretation and release claims.

This is a workflow recommendation, not a claim that one product guarantees better science. Both require the same tested calculations, immutable inputs and stage gates.

Official Codex cloud documentation describes connecting a GitHub repository, configuring an environment, running tasks and reviewing changes. Its agent-phase internet access is disabled by default and configurable separately; setup/network permissions need verification. Do not assume switching modes grants unrestricted data access or retains this conversation. The established GitHub Actions runner remains available.

Sources checked for this handoff:
- https://learn.chatgpt.com/docs/cloud
- https://learn.chatgpt.com/docs/cloud/internet-access

## Prompt for repository-connected code work now

> Read stage1b/docs/execution-plan.md, stage1b/docs/cohort-audit.md, stage1b/docs/NEXT_AGENT.md and stage1b/docs/DECISIONS.md. Current authorization is Stage 1B only. Review the repository and latest returned acquisition evidence; verify checksums first. Implement only necessary Stage 1B acquisition/qualification fixes, execute tests, and regenerate stage1b/PACKAGE_CHECKSUMS.sha256 with stage1b/scripts/update_package_checksums.py after any intentional source change. Do not bypass integrity checks, fabricate outputs, normalize or score treatments, tune a held-out evaluation, or start Stage 2. Preserve source bytes and explicit unresolved metadata. Return a reviewed diff, actual test evidence and checkpoint, not only code. Ask me only for necessary account authorization, artifact transfer, or a spending/scope decision.

After Stage 1 passes, replace the stage authorization with an explicit Stage 2 task and attach the newly approved cohort/checkpoint. Do not reuse the Stage 1-only prompt to start scientific baseline execution.

## Contribution accounting

Keep human project direction, actual scientific decisions, public source methods, AI-assisted code generation and performed validation distinguishable. Provide a walkthrough for the owner to understand and explain the system. Do not invent a manual-development history, unseen lab experiments, or independent peer review.
