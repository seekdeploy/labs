import { expect, it, vi } from 'vitest';

const track = vi.fn();

// Vitest 5 clears mocks between tests (clearMocks: true); count within one test instead.

it('first test calls once', () => {
  track();
  expect(track).toHaveBeenCalledTimes(1);
});

it('second test counts its own call', () => {
  track();
  expect(track).toHaveBeenCalledTimes(1);
});
