import { add } from './math.mjs';

const got = add(2, 3);
if (got !== 5) {
  console.log(`FAIL add(2, 3) expected 5, got ${got}`);
  process.exit(1);
}
console.log('ok add(2, 3) = 5');
