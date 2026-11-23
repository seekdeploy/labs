import { expect, it, vi } from 'vitest';
import { greet } from './greet';

// Literal port of the Jest version: the factory returns the module's default export directly.
vi.mock('./format-name', () => ({ default: () => 'MOCKED' }));

it('uses the mocked default export', () => {
  expect(greet('ada')).toBe('Hello, MOCKED');
});
