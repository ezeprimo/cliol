# AGENTS

Repo-local agent rules for `cliol`.

- Use the local `.venv` for all Python commands.
- Do not install Python packages globally.
- Before claiming a command works, validate with a real CLI invocation (not only unit mocks).
- Keep temporary artifacts out of the repo root and tracked paths.
- All fund-movement operations require the trading gate: TradingGate.check() + prompt_password() in one instance.

Project-local skills available in this repo:
<available_skills>
  <skill>
    <name>cliol-skill</name>
    <description>Trigger: cliol, IOL, invertir online, trading, stocks, portfolio, acciones, cotizaciones, FCI, MEP, CPD, BYMA, BCBA, Argentine market, broker</description>
    <location>file:///mnt/d/MisProyectos/iol/iol-cli/skills/cliol-skill/SKILL.md</location>
  </skill>
</available_skills>
