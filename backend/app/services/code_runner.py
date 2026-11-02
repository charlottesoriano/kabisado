"""Code runner interface: ``run(language, code, stdin, limits)`` ->
``{stdout, stderr, exit_code, time_ms}``. Judge0 hosted API, or wasmtime (``CODE_RUNNER=wasm``).
Used only at generation time. Never ``exec``/``eval``/``subprocess``."""
