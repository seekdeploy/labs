import { defineConfig } from 'vitest/config';

// Separate config for the probe tests I wrote; ms's own config only includes src/.
export default defineConfig({ test: { include: ['probe/**/*.test.ts'] } });
