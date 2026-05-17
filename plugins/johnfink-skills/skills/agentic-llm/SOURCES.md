# Sources for the agentic-llm skill

Reference material the principles in `SKILL.md` were synthesized from. **Not loaded into Claude's context** — kept here for the human reader of the repo.

Roughly in order of how much each one will change your design:

- Anthropic — [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (the workflow/agent distinction, the named patterns: prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer)
- Anthropic — [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Anthropic — [Writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- Anthropic — [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (the 15× cost number, parallel subagent caps, observability/checkpoint patterns)
- OpenAI — [A practical guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)
- Hamel Husain — [Your AI product needs evals](https://hamel.dev/blog/posts/evals/)
- Eugene Yan — [Patterns for LLM systems](https://eugeneyan.com/writing/llm-patterns/)
- [Applied LLMs](https://applied-llms.org/) — the practitioner consensus document
- Simon Willison on the lethal trifecta and prompt injection

## Evidence for §6 (latency vs. accuracy tradeoff)

- Liu et al., "Lost in the Middle" (2023) — LLMs attend best to the start and end of context; middle accuracy drops sharply.
- NIAH (Needle in a Haystack) evals and the RULER benchmark — accuracy degrades with context length even on models claiming 200K+ windows.
- RAG vs. long-context comparison studies — well-tuned retrieval matches or beats stuffing the corpus in context, at lower cost.

## Origin of §2 (queue/decoupling)

Not in the canonical agent essays. It's classical producer/consumer queueing applied to agent invocation — a structural pattern from systems engineering that the agent literature hasn't yet named explicitly.
