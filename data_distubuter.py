import threading
from queue import Queue, Full, Empty

class DataDistributor:
    def __init__(self, consumer_classes, source_queue, consumer_queue_factory, *args, **kwargs):
        self.source_queue = source_queue
        self.consumer_queues = [consumer_queue_factory() for _ in consumer_classes]
        self.consumer_threads = []
        self.consumers = []
        self._stop_event = threading.Event()

        # Create consumer instances and their respective threads
        for queue, consumer_class in zip(self.consumer_queues, consumer_classes):
            consumer = consumer_class(queue, *args, **kwargs)
            thread = threading.Thread(target=consumer.run)
            self.consumers.append(consumer)
            self.consumer_threads.append(thread)

    def start(self):
        # Start the consumer threads
        for thread in self.consumer_threads:
            thread.start()
        # Start the distributor thread
        self.distributor_thread = threading.Thread(target=self.distribute)
        self.distributor_thread.start()

    def distribute(self):
        while not self._stop_event.is_set():
            try:
                data = self.source_queue.get(timeout = 1)
            except Empty:
                continue
            for queue in self.consumer_queues:
                queue.put(data)

    def stop(self):
        # Signal all consumer threads to stop
        for consumer in self.consumers:
            consumer.stop()
        # Wait for all consumer threads to finish
        for thread in self.consumer_threads:
            thread.join()
        # Stop the distributor thread
        self._stop_event.set()
        self.distributor_thread.join()
