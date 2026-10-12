"""Who the digest is for. Edit this to change how the curator agent ranks articles.

The curator reads this as plain text, so write it the way you'd brief a human assistant.
"""

# Used to greet you in the email ("Hey Ethan, ...").
USER_NAME = "Ethan"

USER_PROFILE = f"""\
Name: {USER_NAME}
Role: Software engineer building AI-powered applications in Python.

Most interested in:
- New model releases and capabilities (OpenAI, Anthropic, Google, open-weight models)
- AI coding tools and agents (e.g. Codex, Claude Code), and practical techniques for building with them
- LLM engineering: APIs, structured outputs, RAG, evals, prompt engineering, cost and latency
- Hands-on tutorials and technical deep dives I can apply to my own projects

Somewhat interested in:
- AI research breakthroughs explained for practitioners
- AI safety and security, when it affects how models can be used
- Career topics for AI engineers (freelancing, skills in demand)

Not interested in:
- Enterprise customer case studies and partnership announcements
- Marketing videos and hype without technical substance
- Funding rounds, stock prices and business gossip
"""
