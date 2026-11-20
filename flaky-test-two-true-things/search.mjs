// A search box. Each keystroke sends a request; the reply is shown when it arrives.
// DELIBERATE BUG: a slow reply for an old query can overwrite a newer one.
const fakeServer = (query) =>
  new Promise((resolve) => {
    const latency = Math.random() * 60; // 0 to 60 ms, like a real network
    setTimeout(() => resolve(`results for "${query}"`), latency);
  });

export function createSearchBox() {
  const box = { shown: '', pending: [] };
  box.type = (query) => {
    const request = fakeServer(query).then((results) => {
      box.shown = results;
    });
    box.pending.push(request);
  };
  return box;
}
