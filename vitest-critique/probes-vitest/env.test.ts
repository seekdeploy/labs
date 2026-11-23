import { expect, it } from 'vitest';

const edge = typeof (globalThis as any).EdgeRuntime;
const node = typeof globalThis.process?.versions?.node;

it(`runtime: EdgeRuntime is ${edge}, process.versions.node is ${node}`, () => {
  expect(true).toBe(true);
});
