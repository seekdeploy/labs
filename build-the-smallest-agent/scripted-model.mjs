// A SCRIPTED stand-in for a language model. It is not AI: it plays back
// fixed steps, choosing the next one by reading the conversation so far.
export function model(messages) {
  const results = messages.filter((m) => m.role === 'tool').map((m) => m.content);
  const last = results.at(-1) ?? '';
  const call = (command) => ({ type: 'tool_call', name: 'run_command', input: { command } });

  if (results.length === 0) return call('node test.mjs');
  if (results.length === 1) {
    return last.includes('FAIL') ? call('cat math.mjs') : { type: 'text', text: 'The test already passes.' };
  }
  if (results.length === 2) {
    return last.includes('a - b')
      ? call("sed -i 's/a - b/a + b/' math.mjs")
      : { type: 'text', text: 'I could not find the bug. Stopping.' };
  }
  if (results.length === 3) return call('node test.mjs');
  return last.includes('ok')
    ? { type: 'text', text: 'Fixed: add() subtracted instead of adding. The test passes.' }
    : { type: 'text', text: 'The fix did not work. Stopping.' };
}
