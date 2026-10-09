import importlib.util
import logging
from threading import Lock
from ..schemas import Status

log = logging.getLogger(__name__)

class LazyModel:
    package = ''
    def __init__(self):
        self.instance = None
        self.lock = Lock()
        self.state = 'configured' if importlib.util.find_spec(self.package) else 'unavailable'
        self.detail = 'Loaded on first use' if self.state == 'configured' else f'Install backend/requirements-ml.txt ({self.package} missing)'
    def status(self): return Status(state=self.state, detail=self.detail)
    def inference_failed(self):
        if self.state != 'unavailable':
            self.state, self.detail = 'failed', f'{self.package} inference failed; inspect backend logs'
    def inference_succeeded(self):
        self.state, self.detail = 'ready', 'Checkpoint loaded; last inference successful'
    def get(self):
        with self.lock:
            if self.instance is not None: return self.instance
            if self.state in ('failed', 'unavailable'): raise RuntimeError(self.detail)
            self.state, self.detail = 'loading', 'Downloading/loading checkpoint'
            try:
                self.instance = self.load()
                self.state, self.detail = 'ready', 'Checkpoint loaded'
                return self.instance
            except Exception as exc:
                log.exception('%s initialization failed', self.package)
                self.state, self.detail = 'failed', f'{self.package} initialization failed; inspect backend logs and restart after fixing configuration'
                raise RuntimeError(self.detail) from exc
    def load(self): raise NotImplementedError
