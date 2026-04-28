import asyncio
import contextlib
import multiprocessing
import os
import signal
import sys
from pathlib import Path

from core.database import init_db
from core.logging import configure_logging


async def _stream_output(stream: asyncio.StreamReader | None) -> None:
    if stream is None:
        return
    while True:
        line = await stream.readline()
        if not line:
            return
        sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()


async def _spawn(name: str, *args: str) -> tuple[str, asyncio.subprocess.Process]:
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=os.environ.copy(),
    )
    asyncio.create_task(_stream_output(proc.stdout))
    return name, proc


async def main() -> None:
    multiprocessing.freeze_support()
    configure_logging()
    await init_db()

    stop_event = asyncio.Event()
    children: dict[str, asyncio.subprocess.Process] = {}

    def stop() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop)

    root = Path(__file__).resolve().parents[2]
    for name, proc in await asyncio.gather(
        _spawn('api', str(root / 'packages' / 'backend' / 'main.py')),
        _spawn('scheduler', str(root / 'packages' / 'scheduler' / 'scheduler.py')),
        _spawn('worker-manager', str(root / 'packages' / 'worker-manager' / 'worker.py')),
    ):
        children[name] = proc

    wait_tasks = {asyncio.create_task(proc.wait()): name for name, proc in children.items()}
    stop_task = asyncio.create_task(stop_event.wait())
    done, pending = await asyncio.wait({*wait_tasks.keys(), stop_task}, return_when=asyncio.FIRST_COMPLETED)

    failed_name: str | None = None
    failed_code = 0
    for task in done:
        if task is stop_task:
            continue
        failed_name = wait_tasks[task]
        failed_code = task.result()
        break

    stop_event.set()
    for task in pending:
        task.cancel()
    for proc in children.values():
        if proc.returncode is None:
            proc.send_signal(signal.SIGTERM)
    for proc in children.values():
        with contextlib.suppress(ProcessLookupError):
            await asyncio.wait_for(proc.wait(), timeout=10)
    for proc in children.values():
        if proc.returncode is None:
            proc.kill()
            await proc.wait()

    if failed_name is not None and failed_code != 0:
        raise SystemExit(failed_code)


if __name__ == '__main__':
    asyncio.run(main())
