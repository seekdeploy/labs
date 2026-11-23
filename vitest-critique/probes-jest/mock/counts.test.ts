import { expect, it, jest } from '@jest/globals';

const track = jest.fn();

it('first test calls once', () => {
  track();
  expect(track).toHaveBeenCalledTimes(1);
});

it('second test sees both calls', () => {
  track();
  expect(track).toHaveBeenCalledTimes(2);
});
