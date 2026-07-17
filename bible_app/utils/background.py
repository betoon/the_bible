"""Shared background task runner for UI-safe async work."""

from concurrent.futures import ThreadPoolExecutor

from bible_app.config.settings import BACKGROUND_WORKERS
from bible_app.utils.logger import get_logger


logger = get_logger(__name__)


class BackgroundTaskRunner:
    """Run slow work off the Tkinter UI thread and return callbacks safely."""

    def __init__(self, tk_root, max_workers=BACKGROUND_WORKERS):
        """Create a bounded worker pool.

        Args:
            tk_root: Tk root or widget that provides ``after`` for UI callbacks.
            max_workers: Maximum number of background jobs to run at once.
        """
        self.tk_root = tk_root
        self.executor = ThreadPoolExecutor(max_workers=max(1, int(max_workers)), thread_name_prefix="bible-app")

    def submit(self, work, on_success=None, on_error=None):
        """Submit background work and schedule completion callbacks on Tk.

        Args:
            work: Zero-argument callable to run in the worker pool.
            on_success: Optional callback receiving the returned value.
            on_error: Optional callback receiving the raised exception.

        Returns:
            The ``Future`` created by ``ThreadPoolExecutor``.
        """
        future = self.executor.submit(work)

        def done(completed):
            try:
                result = completed.result()
            except Exception as exc:
                logger.exception("Background task failed")
                if on_error:
                    self.tk_root.after(0, lambda e=exc: on_error(e))
                return
            if on_success:
                self.tk_root.after(0, lambda r=result: on_success(r))

        future.add_done_callback(done)
        return future

    def shutdown(self):
        """Stop accepting work and cancel jobs that have not started."""
        self.executor.shutdown(wait=False, cancel_futures=True)
