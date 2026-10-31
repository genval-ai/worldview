// Guard: every import of worldview's own publisher names a version the repository contains.
//
// This repository is the only source of worldview.genval.ai's versions, so an import of one that
// is not here can only mean it was deleted. Each document is read by the SDK's parser, and versions
// are compared by namespace (publisher/package/version), never by file path.
//
// Retire this guard when worldview's pinned CLI validates at the newest version in each range again
// (Option B): `kanonak hash --offline`, run on each version, then refuses one whose stated versions
// are not all present.
//
// Usage: node own-imports-exist.mjs <publisher-dir>   e.g. kanonak-packages/worldview.genval.ai
import fs from 'node:fs';
import path from 'node:path';
import { KanonakParser } from '@kanonak-protocol/sdk';

const dir = process.argv[2];
const files = [];
(function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p);
    else if (e.name.endsWith('.kan.yml')) files.push(p);
  }
})(dir);

const parser = new KanonakParser();
const v = x => `${x.major}.${x.minor}.${x.patch}`;
const docs = files.map(f => ({ f, m: parser.parse(fs.readFileSync(f, 'utf8')).metadata }));

const present = new Set();
const publishers = new Set();
for (const { m } of docs) {
  const ns = m.namespace_;
  present.add(`${ns.publisher}/${ns.package_}@${v(ns.version)}`);
  publishers.add(ns.publisher);
}

let bad = 0;
for (const { f, m } of docs) {
  for (const i of m.allImports) {
    if (!publishers.has(i.publisher)) continue;
    const want = `${i.publisher}/${i.packageName}@${v(i.version)}`;
    if (!present.has(want)) {
      console.log(`::error file=${f}::Imports ${want} (${i.package_}), which this repository does not contain. Restore that published version.`);
      bad = 1;
    }
  }
}
if (!bad) console.log(`own-imports-exist: every import of ${[...publishers].join(', ')} names a version in the repository (${docs.length} files)`);
process.exit(bad);
