// Fix 2 (the app): only the reply to the latest query may update the screen.
const fakeServer = (query) =>
  new Promise((resolve) => {
    const latency = Math.random() * 60; // 0 to 60 ms, like a real network
    setTimeout(() => resolve(`results for "${query}"`), latency);
  });

export function createSearchBox() {
  const box = { shown: '', pending: [] };
  let latest = 0;
  box.type = (query) => {
    const id = ++latest;
    const request = fakeServer(query).then((results) => {
      if (id === latest) box.shown = results; // drop stale replies
    });
    box.pending.push(request);
  };
  return box;
}
