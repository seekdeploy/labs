// Drive a local Uptime Kuma over its Socket.IO API (the same API its web UI uses).
// Usage:
//   NODE_PATH=<kuma>/node_modules node kuma-ctl.js setup
//   NODE_PATH=<kuma>/node_modules node kuma-ctl.js add-monitor <name> <url> <interval> <maxretries> <retryInterval> <resendInterval>
//   NODE_PATH=<kuma>/node_modules node kuma-ctl.js list
// Credentials are throwaway values for a local test instance.
const { io } = require("socket.io-client");

const URL = process.env.KUMA_URL || "http://127.0.0.1:3001";
const USER = "admin";
const PASS = "local-test-only-1A";

function call(socket, event, ...args) {
    return new Promise((resolve) => socket.emit(event, ...args, resolve));
}

async function connect() {
    const socket = io(URL, { transports: ["websocket"], reconnection: false });
    await new Promise((res, rej) => {
        socket.on("connect", res);
        socket.on("connect_error", rej);
    });
    return socket;
}

async function login(socket) {
    const r = await call(socket, "login", { username: USER, password: PASS, token: "" });
    if (!r.ok) {
        throw new Error("login failed: " + JSON.stringify(r));
    }
}

async function main() {
    const [cmd, ...a] = process.argv.slice(2);
    const socket = await connect();
    try {
        if (cmd === "setup") {
            const need = await call(socket, "needSetup");
            if (need) {
                console.log("setup:", JSON.stringify(await call(socket, "setup", USER, PASS)));
            } else {
                console.log("setup: already done");
            }
            await login(socket);
            const n = await call(socket, "addNotification", {
                name: "local-webhook-pager",
                type: "webhook",
                webhookURL: "http://127.0.0.1:8082/alert",
                webhookContentType: "json",
                isDefault: false,
                applyExisting: false,
            }, null);
            console.log("addNotification:", JSON.stringify(n));
        } else if (cmd === "add-monitor") {
            await login(socket);
            const [name, url, interval, maxretries, retryInterval, resendInterval, notificationId] = a;
            const monitor = {
                name, type: "http", url, method: "GET",
                interval: Number(interval), retryInterval: Number(retryInterval),
                maxretries: Number(maxretries), resendInterval: Number(resendInterval),
                timeout: 10, maxredirects: 10, accepted_statuscodes: ["200-299"],
                notificationIDList: { [notificationId || "1"]: true },
                kafkaProducerBrokers: [], kafkaProducerSaslOptions: {}, conditions: [], rabbitmqNodes: [],
                active: true,
            };
            console.log("add:", JSON.stringify(await call(socket, "add", monitor)));
        } else if (cmd === "list") {
            await login(socket);
            const list = await new Promise((res) => {
                socket.on("monitorList", res);
                socket.emit("getMonitorList", () => {});
            });
            for (const m of Object.values(list)) {
                console.log(m.id, m.name, m.url, "interval", m.interval, "maxretries", m.maxretries, "active", m.active);
            }
        } else {
            console.log("unknown command");
        }
    } finally {
        socket.close();
    }
}

main().catch((e) => {
    console.error(e.message || e);
    process.exit(1);
});
