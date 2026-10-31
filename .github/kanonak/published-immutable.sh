#!/usr/bin/env bash
# Guard: a published package version is never deleted or changed.
#
# A version file is kanonak-packages/<publisher>/<package>/<x.y.z>.kan.yml, or the older flat
# kanonak-packages/<publisher>/<package>@<x.y.z>.kan.yml. If its publisher serves that version, its
# bytes never change and it never goes away: other published versions import it by that exact
# version. A pure rename with identical bytes passes, which is all a layout move should be. A version
# its publisher does not serve (HTTP 404) was never published, so correcting it is allowed; any other
# answer from the publisher fails closed.
#
# Retire this guard when worldview's pinned CLI has `kanonak publish --check`
# (kanonak-protocol/typescript#253), which checks the same thing inside the CLI.
#
# Usage: published-immutable.sh <base-ref> <head-ref>
set -euo pipefail
base="$1"; head="$2"
re='^kanonak-packages/([^/]+)/(([^/@]+)/([0-9]+\.[0-9]+\.[0-9]+)|([^/@]+)@([0-9]+\.[0-9]+\.[0-9]+))\.kan\.yml$'
bad=0

served() {  # prints the HTTP status the publisher returns for the version file at $1
  [[ "$1" =~ $re ]] || { echo none; return; }
  local pub="${BASH_REMATCH[1]}" pkg="${BASH_REMATCH[3]:-${BASH_REMATCH[5]}}" ver="${BASH_REMATCH[4]:-${BASH_REMATCH[6]}}"
  curl -s -o /dev/null -w '%{http_code}' --max-time 20 --retry 2 "https://$pub/$pkg/$ver.kan.yml" || echo 000
}

check() {  # $1 file, $2 what happened
  [[ "$1" =~ $re ]] || return 0
  local code; code=$(served "$1")
  case "$code" in
    404) echo "published-immutable: $1 was $2, but its publisher does not serve it, so it was never published: allowed" ;;
    200) echo "::error file=$1::A published version was $2: $1. Its publisher serves it and other versions import it; restore it and publish a new version instead."; bad=1 ;;
    *)   echo "::error file=$1::$1 was $2, and its publisher answered HTTP $code, so whether it is published is unknown: refusing."; bad=1 ;;
  esac
}

while IFS=$'\t' read -r status a b; do
  case "$status" in
    D)    check "$a" deleted ;;
    M)    check "$a" changed ;;
    R100) ;;
    R*)   check "$a" "moved with changed bytes to $b" ;;
  esac
done < <(git diff --name-status --find-renames=100% "$base" "$head" -- kanonak-packages)
[ "$bad" -eq 0 ] && echo "published-immutable: no published version deleted or changed between $(git rev-parse --short "$base") and $(git rev-parse --short "$head")"
exit "$bad"
