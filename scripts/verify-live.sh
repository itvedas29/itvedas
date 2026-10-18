#!/usr/bin/env bash
# Live verification for itvedas.com cleanup. Run from a normal internet connection.
B=https://www.itvedas.com
pass(){ echo "PASS  $1"; }; fail(){ echo "FAIL  $1  -> $2"; }
blocked(){ echo "BLOCKED  $1  (Cloudflare challenge, check not evaluated)"; }
redir(){ # path expected_target_path label
  out=$(curl -sI -m 20 "$B$1"); code=$(echo "$out"|awk 'NR==1{print $2}'); loc=$(echo "$out"|awk 'tolower($1)=="location:"{print $2}'|tr -d '\r')
  if [ "$code" = "403" ]; then blocked "$3"; return; fi
  if [ "$code" = "301" ] && echo "$loc" | grep -q "$2"; then pass "$3 $code $loc"; else fail "$3" "status=$code location=$loc"; fi; }
echo "== a. longest redirect source"
redir /news/2026-08-30-hackers-hide-backdoor-malware-behind-fake-security-checkpoin 2026-06-26-hackers-hide-dangerous-code /a
echo "== b. near-identical slugs (headlamp cluster)"
redir /news/2026-07-14-making-the-switch-from-kubernetes-dashboard-to-headlamp-what 2026-07-30-making-the-switch-from-kubernetes-dashboard-to-headlamp-what /b1
redir /news/2026-07-18-making-the-switch-from-kubernetes-dashboard-to-headlamp-what 2026-07-30-making-the-switch-from-kubernetes-dashboard-to-headlamp-what /b2
echo "== c. original Kubernetes staged redirects"
redir /news/2026-07-01-kubernetes-leadership-shares-latest-updates-on-container-man 2026-07-04-kubernetes-community-shares /c1
redir /news/2026-07-07-kubernetes-community-shares-latest-platform-updates-and-deve 2026-07-04-kubernetes-community-shares /c2
redir /news/2026-07-09-kubernetes-team-shares-latest-platform-updates-through-offic 2026-08-05-kubernetes-community-shares /c3
echo "== d. noindex on ManageEngine thin pages (expect noindex) and substantive (expect none)"
for p in saas-manager-plus fileanalysis statusiq endpoint-central; do
  h=$(curl -s -m 20 "$B/manageengine/$p"); if echo "$h" | grep -q "Just a moment"; then r=BLOCKED; elif echo "$h" | grep -qi 'name="robots" content="noindex,follow"'; then r=noindex; else r=NONE; fi
  echo "$p robots=$r"; done
echo "== e. category label links on fixed articles"
for a in 2026-06-17-complete-networking-guide:networking 2026-07-07-cloud:cloud 2026-06-20-operating-systems:linux; do
  s=${a%%:*}; c=${a##*:}
  h=$(curl -s -m 20 "$B/articles/$s"); lbl=$(echo "$h" | grep -o 'Category:</strong> <a href="[^"]*"[^>]*>[^<]*' | head -1)
  hub=$(curl -s -o /dev/null -w "%{http_code}" -m 20 "$B/articles/$c/")
  echo "$s label: $lbl  hub:/articles/$c/ -> $hub"; done
echo "== f. sitemap"
curl -s -m 20 "$B/sitemap.xml" | grep -c "<url>"
echo "== g. drafts no longer deployed (expect 404)"
curl -s -o /dev/null -w "%{http_code}\n" -m 20 "$B/drafts/manageengine-affiliate/index.html"
echo "== h. affiliate disclosure gone from a thin page (expect 0)"
h=$(curl -s -m 20 "$B/manageengine/saas-manager-plus"); if echo "$h" | grep -q "Just a moment"; then echo BLOCKED; else echo "$h" | grep -ci "may earn a commission" || true; fi
exit 0
