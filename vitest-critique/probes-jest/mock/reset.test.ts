import { expect, it, jest } from '@jest/globals';

it('mockReset forgets the implementation', () => {
  const fn = jest.fn(() => 'original');
  fn.mockReset();
  expect(fn()).toBeUndefined();
});
