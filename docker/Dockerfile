# Stage 1: Build the binary with PyInstaller
FROM python:3.12-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends binutils && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pyinstaller==6.11.0 pyiol-client typer rich bcrypt platformdirs "tomli>=2.0.0" tomli-w

COPY pyproject.toml /app/
COPY src/ /app/src/
COPY cliol/ /app/cliol/
WORKDIR /app

RUN python -m PyInstaller \
    --onefile \
    --name cliol-linux-amd64 \
    --add-data "cliol:cliol" \
    --hidden-import typer \
    --hidden-import rich \
    --hidden-import bcrypt \
    --hidden-import platformdirs \
    --collect-all typer \
    --collect-all rich \
    src/cliol/__main__.py

# Stage 2: Minimal runtime
FROM debian:bookworm-slim

RUN useradd --create-home --shell /bin/bash cliol
USER cliol
WORKDIR /home/cliol

COPY --from=builder /app/dist/cliol-linux-amd64 /usr/local/bin/cliol

ENTRYPOINT ["cliol"]
CMD ["--help"]
