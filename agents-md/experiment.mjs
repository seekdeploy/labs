// Does a small local model plan a change better with AGENTS.md in its context?
// Usage: node experiment.mjs <model.gguf> <repo-dir> <AGENTS.md> <runs> <out.json>
import fs from 'node:fs';
import {getLlama, LlamaChatSession} from 'node-llama-cpp';

const [modelPath, repo, agentsPath, runs = '10', outPath = 'results.json'] = process.argv.slice(2);

const files = fs.readdirSync(repo).filter((f) => !['.git', 'node_modules'].includes(f)).sort();
const packageJson = fs.readFileSync(`${repo}/package.json`, 'utf8');
const agentsMd = fs.readFileSync(agentsPath, 'utf8');

const system = 'You are a coding agent working in a repository. Reply with a short plan: '
	+ 'the files you will edit, then the exact shell commands you will run to check your work. '
	+ 'Do not write the code.';
const task = 'Task: add a new option `maxLength` (number) that truncates the slug to at most that many characters.';

const context = (withAgents) => [
	`Repository files: ${files.join(', ')}`,
	`package.json:\n${packageJson}`,
	...(withAgents ? [`AGENTS.md:\n${agentsMd}`] : []),
	task,
].join('\n\n');

// The checklist. Each check is a regex over the lowercased reply.
export const checks = {
	'edits index.js': /index\.js/,
	'edits index.d.ts': /index\.d\.ts/,
	'edits readme.md': /readme/,
	'edits test.js': /test\.js/,
	'runs npm test': /npm (run )?test/,
	'no other test runner': (t) => !/jest|mocha|vitest|ava\b/.test(t),
	// Added after the smoke run: naming the right files is not enough if the plan also edits the wrong ones.
	'leaves other files alone': (t) => !/\.editorconfig|\.gitignore|\.gitattributes|\.npmrc|\.github|license|package\.json/.test(t),
};

const score = (text) => {
	const t = text.toLowerCase();
	return Object.fromEntries(Object.entries(checks).map(([name, c]) => [name, c instanceof RegExp ? c.test(t) : c(t)]));
};

const llama = await getLlama();
const model = await llama.loadModel({modelPath});
const results = [];

for (const withAgents of [false, true]) {
	for (let seed = 1; seed <= Number(runs); seed++) {
		const ctx = await model.createContext({contextSize: 4096});
		const session = new LlamaChatSession({contextSequence: ctx.getSequence(), systemPrompt: system});
		const started = Date.now();
		const reply = await session.prompt(context(withAgents), {temperature: 0.7, seed, maxTokens: 400});
		results.push({withAgents, seed, seconds: (Date.now() - started) / 1000, checks: score(reply), reply});
		console.log(`${withAgents ? 'with   ' : 'without'} seed ${seed}: ${Object.values(score(reply)).filter(Boolean).length}/7`);
		await ctx.dispose();
	}
}

fs.writeFileSync(outPath, JSON.stringify({modelPath: modelPath.split('/').at(-1), runs: Number(runs), results}, null, '\t'));
