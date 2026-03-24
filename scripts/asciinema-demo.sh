#!/usr/bin/env bash
# Recorded by: uvx --from asciinema asciinema rec -c "bash scripts/asciinema-demo.sh" demo.cast
set -euo pipefail
cd "$(dirname "$0")/.."
BODY='{"startTime":"2026-03-24","endTime":"2026-03-24","province":"北京"}'

prompt() {
  printf '%s\n' "$@"
}

prompt "# 1) Chart statistics for Beijing on 2026-03-24"
prompt '$ uv run main.py search --body-json '"'"$BODY"'"' --pretty'
# stderr quiet when stdout is closed early (head)
uv run main.py search --body-json "$BODY" --pretty 2>/dev/null | head -n 80

prompt ""
prompt "# 2) List observation cards; pick first report id"
prompt '$ uv run main.py search --report --body-json '"'"$BODY"'"' --pretty | head -n 45'
uv run main.py search --report --body-json "$BODY" --pretty 2>/dev/null | head -n 45

REPORT_ID="$(uv run main.py search --report --body-json "$BODY" 2>/dev/null \
  | uv run python -c "import json,sys; d=json.load(sys.stdin); print(d['report'][0]['id'])")"

prompt ""
prompt "# 3) Full bundle for report id ${REPORT_ID}"
prompt '$ uv run main.py report --id '"${REPORT_ID}"' --pretty | head -n 55'
uv run main.py report --id "${REPORT_ID}" --pretty 2>/dev/null | head -n 55

prompt ""
prompt "# 4) Species checklist filter: query hx (pinyin / initials / name)"
prompt '$ uv run main.py taxon -q hx --pretty | head -n 40'
uv run main.py taxon -q hx --pretty 2>/dev/null | head -n 40

prompt ""
prompt "# done"
