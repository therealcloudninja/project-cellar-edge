# Start from an official, minimal Python image rather than
# building an OS + Python from scratch.
FROM python:3.12-slim

# Where the app will live inside the container.
WORKDIR /app

# Copy only the dependency file first, not the whole project yet.
# This layer only re-runs if pyproject.toml changes — copying
# source code separately, after this, means code-only changes
# don't force a slow dependency reinstall on every rebuild.
COPY pyproject.toml .
COPY src/ src/

# Install the dependencies (and the package itself) in normal,
# non-editable mode — unlike your dev venv, this container is a
# fixed, self-contained artifact, not something you're actively
# editing from inside.
RUN pip install --no-cache-dir .

# Run the orchestration loop — the one thing this container
# actually does, forever, until stopped.
CMD ["python", "-m", "edge_collector.runner"]
