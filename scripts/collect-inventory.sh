#!/usr/bin/env bash
# collect-inventory.sh — self-documenting install map for a CNJ Mesh Pi.
#
# Enumerates Docker containers and non-default (user-installed) systemd services,
# and for each one reports WHERE it lives and HOW it's launched — install path,
# config location, image, mounts, ports, ExecStart. Emits Markdown to stdout.
#
# Usage:
#   ./collect-inventory.sh > install-map-$(hostname).md
# Then commit the file to the repo. Re-run any time things change to refresh.
#
# Read-only: inspects, never modifies. Safe to run anytime. Some Docker details
# need root — run with sudo for complete output (script still works without it,
# just with less container detail).

set -uo pipefail

HOST="$(hostname)"
NOW="$(date '+%Y-%m-%d %H:%M:%S %Z')"

echo "# Install Map — \`${HOST}\`"
echo
echo "_Generated ${NOW} by \`scripts/collect-inventory.sh\`. Re-run to refresh — do not hand-edit._"
echo

# ---------------------------------------------------------------------------
# DOCKER CONTAINERS
# ---------------------------------------------------------------------------
echo "## Docker containers"
echo
if command -v docker >/dev/null 2>&1; then
  names="$(docker ps -a --format '{{.Names}}' 2>/dev/null | sort)"
  if [ -z "$names" ]; then
    echo "_None found (or Docker not accessible without sudo)._"
  else
    while IFS= read -r c; do
      [ -z "$c" ] && continue
      state="$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo '?')"
      image="$(docker inspect -f '{{.Config.Image}}' "$c" 2>/dev/null || echo '?')"
      restart="$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$c" 2>/dev/null || echo '?')"
      # compose project + working dir (if started via compose)
      proj="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$c" 2>/dev/null || true)"
      cfgdir="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project.working_dir"}}' "$c" 2>/dev/null || true)"
      echo "### \`${c}\`  _(state: ${state}, restart: ${restart})_"
      echo
      echo "- **Image:** \`${image}\`"
      [ -n "${proj}" ] && echo "- **Compose project:** \`${proj}\`"
      [ -n "${cfgdir}" ] && echo "- **Compose working dir:** \`${cfgdir}\`  ← compose file lives here"
      # Port mappings
      ports="$(docker inspect -f '{{range $p, $conf := .NetworkSettings.Ports}}{{if $conf}}{{(index $conf 0).HostPort}}->{{$p}} {{end}}{{end}}' "$c" 2>/dev/null || true)"
      [ -n "${ports}" ] && echo "- **Ports:** \`${ports}\`"
      # Bind mounts = where config/data lives on the host
      mounts="$(docker inspect -f '{{range .Mounts}}{{if eq .Type "bind"}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}{{end}}' "$c" 2>/dev/null || true)"
      if [ -n "${mounts}" ]; then
        echo "- **Host bind mounts (config/data on disk):**"
        while IFS= read -r m; do [ -n "$m" ] && echo "    - \`${m}\`"; done <<< "$mounts"
      fi
      # Devices (USB serial, etc.)
      devs="$(docker inspect -f '{{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}' "$c" 2>/dev/null || true)"
      [ -n "${devs// /}" ] && echo "- **Devices:** \`${devs}\`"
      # Config-relevant env (filtered — no secrets dumped wholesale, but show config keys)
      env="$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$c" 2>/dev/null | grep -iE 'PORT|HOST|BROKER|PATH|CONFIG|DEVICE|TOPIC|URL|DIR' | grep -ivE 'PASSWORD|TOKEN|SECRET|KEY=' || true)"
      if [ -n "${env}" ]; then
        echo "- **Config env (secrets omitted):**"
        while IFS= read -r e; do [ -n "$e" ] && echo "    - \`${e}\`"; done <<< "$env"
      fi
      echo
    done <<< "$names"
  fi
else
  echo "_Docker not installed on this host._"
fi
echo

# ---------------------------------------------------------------------------
# SYSTEMD SERVICES (user-installed only — filter OS/vendor noise)
# ---------------------------------------------------------------------------
echo "## systemd services & timers (user-installed)"
echo
echo "_Only units whose file lives under \`/etc/systemd/system\` (i.e. you/we installed them) — OS/vendor units under /lib and /usr/lib are excluded._"
echo
found=0
for unit in $(systemctl list-unit-files --type=service,timer --no-legend 2>/dev/null | awk '{print $1}' | sort -u); do
  frag="$(systemctl show -p FragmentPath --value "$unit" 2>/dev/null || true)"
  # Only report units we installed (live in /etc/systemd/system), skip OS/vendor + symlinked template noise
  case "$frag" in
    /etc/systemd/system/*) : ;;
    *) continue ;;
  esac
  found=1
  state="$(systemctl is-enabled "$unit" 2>/dev/null || echo '?')/$(systemctl is-active "$unit" 2>/dev/null || echo '?')"
  echo "### \`${unit}\`  _(${state})_"
  echo
  echo "- **Unit file:** \`${frag}\`"
  for prop in ExecStart WorkingDirectory EnvironmentFile; do
    val="$(systemctl show -p "$prop" --value "$unit" 2>/dev/null || true)"
    [ -n "${val}" ] && [ "${val}" != "[not set]" ] && echo "- **${prop}:** \`${val}\`"
  done
  echo
done
[ "$found" -eq 0 ] && echo "_None found under /etc/systemd/system._"
echo

# ---------------------------------------------------------------------------
# QUICK NOTES
# ---------------------------------------------------------------------------
echo "## Notes"
echo
echo "- **Config location tip:** for services, the config is usually a path in the ExecStart args (e.g. Graywolf's \`-config /var/lib/graywolf/graywolf.db\`) or an EnvironmentFile above. For containers, it's the host bind mounts."
echo "- Secrets (PASSWORD/TOKEN/SECRET/KEY) are intentionally omitted from env output — safe to commit."
echo "- Re-run and re-commit after any install/move so this never drifts from reality."
