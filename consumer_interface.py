from abc import ABC, abstractmethod
from queue import Queue, Empty
import threading

class ConsumerInterface(ABC):
    def __init__(self, queue: Queue):
        self.queue = queue
        self._stop_event = threading.Event()

    @abstractmethod
    def run(self):
        pass

    def stop(self):
        self._stop_event.set()
