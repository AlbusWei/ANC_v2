# QA - TOOLS

## Allowed Skills

- meta.qa.test-designer
- meta.qa.llm-judge
- sys.qa.test-compiler
- sys.qa.evaluation-runner
- sys.qa.verdict-normalizer
- sys.qa.regression-runner
- sys.qa.hold-triage

## Related Skills (Cross-Agent)

- sys.bpm.process-instance-manager (owned by bpm)
- sys.bpm.escalation-handler (owned by bpm)

## Responsibilities

1. Execute AP-005/018/019 for preparation bundle production.
2. Execute AP-007/008/009/020 for unified gate decision.
3. Execute AP-021/022/023 for hold triage.
4. Emit structured verdict with traceable evidence references.

## Usage Notes

1. Subjective evaluation (AP-008) defaults to enabled.
2. Any P0 fail blocks release.
3. If evidence is missing or unparseable, fail-closed.
