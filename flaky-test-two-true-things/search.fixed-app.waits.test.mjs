import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createSearchBox } from './search.fixed.mjs';

// Fix 1 (the test): wait for every reply instead of a fixed 40 ms.
test('shows results for the latest query', async () => {
  const box = createSearchBox();
  box.type('pen');
  box.type('pens');
  await Promise.all(box.pending);
  assert.equal(box.shown, 'results for "pens"');
});
