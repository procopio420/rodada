#!/usr/bin/env bash
# Require the full expected class/method count, and reject instrumentation errors
# even if an earlier success marker is also present in a combined output.
android_instrumentation_succeeded() {
  local output="$1" expected="$2"
  [[ "$expected" =~ ^[1-9][0-9]*$ ]] || return 1
  if grep -Eqi 'FAILURES!!!|FAILURE:|INSTRUMENTATION_FAILED|INSTRUMENTATION_ABORTED|INSTRUMENTATION_RESULT: (shortMsg|longMsg)=|Process crashed|Tests failed' <<<"$output"; then
    return 1
  fi
  grep -Eq "^[[:space:]]*OK \(${expected} tests?\)[[:space:]]*$" <<<"$output"
}
