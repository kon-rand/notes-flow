# Draft: Writing a Custom Agent

## Requirements (to be confirmed)
- What type of agent? (e.g., chat, web crawler, data processor, etc.)
- What platform/environment? (Node.js, Python, Go, etc.)
- What functionality/purpose? (e.g., fetch data, process user input, automate tasks, etc.)
- Any integration requirements? (APIs, databases, messaging queues)
- Desired interface? (CLI, web UI, library API)
- Expected performance/scale? (single use, background job, high concurrency)
- Testing and deployment considerations?

## Technical Decisions (tentative)
- Language: Node.js (TypeScript) or Python
- Framework: Express for HTTP, or a custom event loop
- Agent pattern: event-driven, worker pool
- Configuration: YAML/JSON config file
- Dependency management: npm / pip
- Testing framework: Jest / PyTest
- Deployment: Docker container

## Open Questions
- Which language do you prefer?
- What is the agent’s primary task?
- Should it run as a standalone service or embedded library?
- Any specific libraries or frameworks you want to use?

## Scope
- IN: Basic agent skeleton, core interfaces, example usage
- OUT: Full production-ready deployment, advanced features like auto-scaling

