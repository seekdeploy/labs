import { expect, it, jest } from '@jest/globals';
import { greet } from './greet';

// Jest docs style: the factory returns the module's default export directly.
jest.mock('./format-name', () => () => 'MOCKED');

it('uses the mocked default export', () => {
  expect(greet('ada')).toBe('Hello, MOCKED');
});
