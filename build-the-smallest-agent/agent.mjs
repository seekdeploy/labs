import { execSync } from 'node:child_process';
import { model } from './scripted-model.mjs';

// The one tool: run a shell command in the project folder.
const tools = {
  run_command: ({ command }) => {
    try {
      return execSync(command, { cwd: 'project', encoding: 'utf8' }) || '(no output)';
    } catch (err) {
      return `exit ${err.status}\n${err.stdout}${err.stderr}`;
    }
  },
};

const messages = [{ role: 'user', content: 'The test in this project fails. Fix it.' }];

for (let turn = 1; turn <= 10; turn++) {
  const reply = model(messages);           // 1. ask the model
  messages.push({ role: 'assistant', content: reply });

  if (reply.type === 'text') {             // 2. no tool call: done
    console.log(`\n[agent] ${reply.text}`);
    break;
  }

  const output = tools[reply.name](reply.input);   // 3. run the tool
  console.log(`\n[turn ${turn}] ${reply.name}: ${reply.input.command}\n${output.trim()}`);
  messages.push({ role: 'tool', name: reply.name, content: output });  // 4. feed it back
}
