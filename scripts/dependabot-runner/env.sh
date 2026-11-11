# Omgeving voor elk Bash-commando van een autonome run, via CLAUDE_ENV_FILE.
# De runner zet PATH (met Node uit .nvmrc) al klaar. SDKMAN volgt hier elke keer .sdkmanrc,
# zodat een nieuwe versie uit stap 3 van de skill meteen geldt, en installeert wat ontbreekt.
# Dit bestand staat in de vault en niet in ~/dependabot-runs, want daar mag de run schrijven.
export SDKMAN_DIR="$HOME/.sdkman"
. "$SDKMAN_DIR/bin/sdkman-init.sh" >/dev/null 2>&1
if [ -f .sdkmanrc ]; then
  sdk env >/dev/null 2>&1 || sdk env install </dev/null >/dev/null 2>&1
fi
