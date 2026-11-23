# timed <label> <command...>: run a command, append "run,label,seconds" to $WORK/timings.csv
timed() {
  local label=$1; shift
  local t0 t1; t0=$(date +%s.%N)
  "$@"
  t1=$(date +%s.%N)
  printf '%s,%s,%.2f\n' "${RUN:-1}" "$label" "$(echo "$t1 - $t0" | bc)" | tee -a "$WORK/timings.csv"
}
