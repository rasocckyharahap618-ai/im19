# UGAI Agent Runtime

Evidence-first orchestration runtime. Python 3.11+. Install with `pip install -e '.[dev,api]'`. Copy `.env.example` to `.env`; provider keys and model IDs are environment-only. SQLite is the initial persistence backend. API task submission is explicitly accepted-but-not-dispatched until a worker is configured.

## Commands
`make install`, `make test`, `make run`, `make migrate`.
