import { expect, it } from 'vitest';
import { increment } from './counter';

it('starts from a fresh module', () => {
  expect(increment()).toBe(1);
});
