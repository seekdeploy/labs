// Runs the test file N times in fresh processes and tallies the failures.
import { spawnSync } from 'node:child_process';

const [file = 'search.test.mjs', runs = '200'] = process.argv.slice(2);
const tally = {};
for (let i = 0; i < Number(runs); i++) {
  const r = spawnSync('node', ['--test', '--test-reporter=tap', file], { encoding: 'utf8' });
  const actual = r.stdout.match(/actual: (.*)/)?.[1] ?? '(passed)';
  tally[actual] = (tally[actual] ?? 0) + 1;
}
console.log(`${file}: ${runs} runs`);
for (const [actual, n] of Object.entries(tally)) console.log(`  ${String(n).padStart(4)}  ${actual}`);
