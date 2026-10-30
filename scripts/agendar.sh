#!/bin/bash
# Agenda o pipeline toda segunda-feira às 7h com o launchd (o agendador do macOS).
# Para desfazer: launchctl unload ~/Library/LaunchAgents/com.nextstepsp.pipeline.plist && rm esse arquivo.
set -euo pipefail
cd "$(dirname "$0")/.."
PLIST="$HOME/Library/LaunchAgents/com.nextstepsp.pipeline.plist"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs/next-step-sp"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.nextstepsp.pipeline</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$(pwd)/scripts/pipeline_agendado.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/next-step-sp/launchd.err</string>
</dict>
</plist>
PLIST

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "Agendado: toda segunda às 7h. Logs em ~/Library/Logs/next-step-sp/"
