#!/bin/sh
# SaveOnSub cloud work computer: read-only, non-secret preflight.
# No sudo, package changes, network calls, environment dumps, process arguments or writes.
set -eu

line() { printf '%s=%s\n' "$1" "$2"; }
status_for() {
  if command -v systemctl >/dev/null 2>&1; then
    state=$(systemctl is-active "$1" 2>/dev/null || true)
    [ -n "$state" ] || state=unknown
  else
    state=systemctl_unavailable
  fi
  line "service_$2" "$state"
}
present() {
  if command -v "$1" >/dev/null 2>&1; then
    line "has_$2" yes
  else
    line "has_$2" no
  fi
}
printf 'SOS_WORK_COMPUTER_PREFLIGHT_V1\n'
line "mode" "read_only"
line "time_utc" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
line "os_kernel" "$(uname -s)"
line "architecture" "$(uname -m)"
line "user_uid" "$(id -u)"
if [ -r /etc/os-release ]; then
  os=$(grep -m 1 '^PRETTY_NAME=' /etc/os-release | cut -d = -f 2- | tr -d '"' || true)
  [ -n "$os" ] || os=unknown
  line "os_pretty" "$os"
fi
if [ -r /proc/meminfo ]; then
  mem=$(grep -m 1 '^MemTotal:' /proc/meminfo | awk '{print $2}' || true)
  [ -n "$mem" ] || mem=unknown
  line "mem_total_kib" "$mem"
fi
if command -v nproc >/dev/null 2>&1; then
  line "logical_cpu_count" "$(nproc)"
fi
if command -v df >/dev/null 2>&1; then
  free_root=$(df -Pk / 2>/dev/null | awk 'NR==2 {print $4}' || true)
  [ -n "$free_root" ] || free_root=unknown
  line "disk_root_available_kib" "$free_root"
fi
for cmd in python3 git node npm cloudflared tailscale podman docker sqlite3 wrangler; do
  present "$cmd" "$cmd"
done
status_for ssh ssh
status_for sshd sshd
status_for xrdp xrdp
status_for tailscaled tailscaled
status_for cloudflared cloudflared
status_for docker docker
status_for podman podman
if [ -d /srv/tenants/sos ]; then
  line "sos_workdir_exists" yes
else
  line "sos_workdir_exists" no
fi
line "secrets_printed" no
printf 'RESULT=OBSERVATION_ONLY_NO_CHANGES\n'
