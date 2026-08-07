#!/usr/bin/env bash
set -euo pipefail

REPO="${CLIOL_REPO:-ezeprimo/cliol}"
INSTALL_DIR="${CLIOL_INSTALL_DIR:-$HOME/.local/bin}"
TARGET_PATH="$INSTALL_DIR/cliol"
PROFILE_FILE="${CLIOL_PROFILE_FILE:-$HOME/.profile}"
STANZA_BEGIN="# >>> cliol installer path >>>"
STANZA_END="# <<< cliol installer path <<<"

FORCE=0; DRY_RUN=0
for arg in "$@"; do case "$arg" in --force|-f) FORCE=1;; --dry-run|-n) DRY_RUN=1;; esac; done

REMOVED=0
info()  { printf '\e[36m%s\e[0m\n' "$1"; }
ok()    { printf '  \e[32m[removed]\e[0m %s\n' "$1"; REMOVED=1; }
skip()  { printf '  \e[33m[skipped]\e[0m %s\n' "$1"; }
absent(){ printf '  \e[90m[absent]\e[0m  %s\n' "$1"; }
dry()   { printf '  \e[35m[dry-run]\e[0m would %s\n' "$1"; }
warn()  { printf '\e[33mWARNING:\e[0m %s\n' "$1" >&2; }

if [[ "$FORCE" -ne 1 ]]; then
  echo "This will remove cliol and clean up shell configuration."
  read -rp "Continue? [y/N] " answer
  if [[ ! "$answer" =~ ^[Yy] ]]; then echo "Cancelled."; exit 0; fi
fi

info "=== cliol uninstall ==="

# Remove binary
if [[ -f "$TARGET_PATH" ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then dry "remove $TARGET_PATH"
  else rm -f "$TARGET_PATH"; ok "$TARGET_PATH"; fi
else absent "$TARGET_PATH"; fi

# Clean PATH stanza from profile files
for profile in "$PROFILE_FILE" "$HOME/.bashrc" "$HOME/.zshrc"; do
  if [[ -f "$profile" ]] && grep -Fq "$STANZA_BEGIN" "$profile"; then
    if [[ "$DRY_RUN" -eq 1 ]]; then dry "clean stanza from $profile"
    else
      sed -i "/$STANZA_BEGIN/,/$STANZA_END/d" "$profile"
      ok "stanza removed from $profile"
    fi
  fi
done

# Clean session PATH
CLEANED_PATH=""
IFS=':' read -ra PATH_ENTRIES <<< "$PATH"
for entry in "${PATH_ENTRIES[@]}"; do
  if [[ "$entry" != "$INSTALL_DIR" ]]; then
    CLEANED_PATH="${CLEANED_PATH}${CLEANED_PATH:+:}$entry"
  fi
done
if [[ "$CLEANED_PATH" != "$PATH" ]]; then export PATH="$CLEANED_PATH"; echo "  Session PATH cleaned."; fi

# Remove empty install directory
if [[ -d "$INSTALL_DIR" ]] && [[ -z "$(ls -A "$INSTALL_DIR" 2>/dev/null)" ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then dry "remove empty $INSTALL_DIR"
  else rmdir "$INSTALL_DIR" 2>/dev/null && ok "empty directory $INSTALL_DIR" || skip "$INSTALL_DIR (not empty)"; fi
fi

if [[ "$REMOVED" -eq 1 ]]; then echo; echo "Uninstall complete. Run 'cliol' again to verify removal."; fi
echo; echo "To reinstall: curl -fsSL https://raw.githubusercontent.com/$REPO/main/install.sh | bash"
