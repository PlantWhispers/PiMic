from queue import Queue
from consumer_interface import ConsumerInterface


class PrintData(ConsumerInterface):
    def __init__(self, queue: Queue):
        super().__init__(queue)

    def run (self):
        while not self._stop_event.is_set() or not self.queue.empty():
            audio_chunk = self.queue.get()
            print(audio_chunk.tobytes())