import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createSearchBox } from './search.fixed.mjs';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// DELIBERATELY FLAKY: waits a fixed 40 ms instead of waiting for the replies.
test('shows results for the latest query', async () => {
  const box = createSearchBox();
  box.type('pen');
  box.type('pens');
  await sleep(40);
  assert.equal(box.shown, 'results for "pens"');
});
