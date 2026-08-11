#!/usr/bin/env node
// Deploy ITVedas Services to Cloudflare Pages.
//
// WHY THIS EXISTS — do not replace it with a bare `wrangler pages deploy`.
//
// This project has no build step, so the source directory IS the publish
// directory. `wrangler pages deploy` publishes every file in that directory,
// which on 2026-08-10 put .dev.vars (a bootstrap token), wrangler.toml (the D1
// and KV IDs), .env.example and the full migrations/*.sql schema on the public
// internet. Confirmed by fetching them, then fixed by deploying only the files
// below. `.assetsignore` does NOT work for `wrangler pages deploy` — it was
// tried first and every excluded file was still served with a 200.
//
// The list is an ALLOWLIST on purpose. A denylist silently publishes whatever
// new file someone drops in the directory next; an allowlist fails closed.
//
// Node stdlib only — no npm dependency, consistent with the project.
//
//   node deploy.mjs            deploy to production (branch: main)
//   node deploy.mjs --dry-run  stage and list files, deploy nothing

import { cpSync, mkdtempSync, rmSync, existsSync, readdirSync, statSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const SRC = dirname(fileURLToPath(import.meta.url));
const DRY = process.argv.includes('--dry-run');

// Everything the public site needs, and nothing else.
const PUBLISH = [
  // top-level pages
  '404.html', 'about.html', 'case-studies.html', 'faq.html', 'how-it-works.html',
  'index.html', 'pricing.html', 'privacy-policy.html', 'request-it-help.html',
  'terms-of-service.html',
  // directories
  'admin', 'assets', 'css', 'js', 'request-it-help', 'services', 'functions',
  // routing / SEO / headers
  '_headers', '_redirects', 'robots.txt', 'sitemap.xml',
];

// Anything matching these must never reach the edge, even if added to PUBLISH
// by mistake. Second line of defence, checked after staging.
const FORBIDDEN = [/^\.dev\.vars$/, /^\.env/, /^wrangler\.toml$/, /^migrations$/, /^\.wrangler$/, /\.sql$/i];

const stage = mkdtempSync(join(tmpdir(), 'itvedas-services-'));
let copied = 0;

try {
  for (const item of PUBLISH) {
    const from = join(SRC, item);
    if (!existsSync(from)) continue;              // _redirects is optional
    cpSync(from, join(stage, item), { recursive: true });
    copied++;
  }

  // Fail closed: re-scan what was actually staged.
  const walk = dir => readdirSync(dir).flatMap(name => {
    const full = join(dir, name);
    return statSync(full).isDirectory() ? walk(full) : [name];
  });
  const staged = readdirSync(stage);
  const leaked = [...staged, ...walk(stage)].filter(n => FORBIDDEN.some(re => re.test(n)));
  if (leaked.length) {
    throw new Error('Refusing to deploy — sensitive files staged: ' + [...new Set(leaked)].join(', '));
  }

  console.log(`Staged ${copied} entries at ${stage}`);
  if (DRY) {
    console.log('Top level:', staged.sort().join(', '));
    console.log('--dry-run: nothing deployed.');
  } else {
    // shell:true is required on Windows — npx resolves to npx.cmd, which
    // spawnSync cannot execute directly without a shell.
    const res = spawnSync(
      'npx',
      ['wrangler', 'pages', 'deploy', `"${stage}"`,
       '--project-name=itvedas-services', '--branch=main', '--commit-dirty=true'],
      { cwd: SRC, stdio: 'inherit', shell: true }  // cwd = SRC so wrangler.toml supplies the bindings
    );
    if (res.status !== 0) {
      console.error(`\nDeploy failed (exit ${res.status}).`);
      process.exit(res.status ?? 1);
    }
    console.log('\nDeployed. Verify no config/secrets leaked:');
    console.log('  curl -s -o /dev/null -w "%{http_code}" https://itvedas-services.pages.dev/wrangler.toml   # expect 404');
  }
} finally {
  rmSync(stage, { recursive: true, force: true });
}
