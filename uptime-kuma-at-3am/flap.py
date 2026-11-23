"""Toggle ./state/target between up and down every N seconds for a fixed duration,
logging each change to ./logs/target-changes.log. The target server keeps running."""
import pathlib, sys, time
HERE = pathlib.Path(__file__).resolve().parent
STATE = HERE / "state" / "target"; LOG = HERE / "logs" / "target-changes.log"
period, duration = float(sys.argv[1]), float(sys.argv[2])
end = time.time() + duration
while time.time() < end:
    time.sleep(period)
    s = "down" if STATE.read_text().strip() == "up" else "up"
    STATE.write_text(s)
    with open(LOG, "a") as f: f.write(f"{time.strftime('%FT%TZ', time.gmtime())} target -> {s}\n")
STATE.write_text("up")
with open(LOG, "a") as f: f.write(f"{time.strftime('%FT%TZ', time.gmtime())} target -> up (flapping stopped)\n")
