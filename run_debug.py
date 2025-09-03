# run_debug.py
import runpy
import sys
import traceback

import debugpy

try:
    print(
        "debugpy: attempting to listen on 5678 — attach your debugger now", flush=True
    )
    debugpy.log_to("debugpy.log")
    debugpy.listen(5678)
    print("debugpy: listen() returned, now waiting for client...", flush=True)
    debugpy.wait_for_client()
    attached = debugpy.is_client_connected()
    print("debugpy client attached?", attached)
    print("debugpy: client attached — continuing to run main.py", flush=True)

    # Forward CLI args to main.py
    sys.argv = ["main.py"] + sys.argv[1:]
    runpy.run_path("main.py", run_name="__main__")
except Exception:
    print("Exception in run_debug.py:", flush=True)
    traceback.print_exc()
    # keep process alive a bit so you can see messages in console
    try:
        import time

        time.sleep(3)
    except Exception:
        pass
    raise
