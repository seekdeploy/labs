import { expect, it, vi } from 'vitest';

it('mockReset restores the original implementation', () => {
  const fn = vi.fn(() => 'original');
  fn.mockReset();
  expect(fn()).toBe('original'); // Vitest: back to the original, not undefined
});
