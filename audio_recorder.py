"""
Implementation Context:

- SamplingRate: 384kHz
  - Reason: To capture high-frequency sounds from plants.
  - Impact: Increases CPU and storage requirements.

- Language: Python
  - Reason: Portability and ease of use.
  - Impact: Slower execution speed, optimized via threading.

- MemoryStrategy: TempFile
  - Reason: To manage large data sizes.
  - Impact: Requires file operations to convert to final format.

- FileFormat: WAV
  - Reason: Lossless audio storage.
  - Impact: Larger file size, header manipulation needed.

- FileOperation: SameDevice
  - Reason: Faster file moving operations.
  - Impact: Limits storage options to a single device.

- Threading: Multi
  - Reason: To separate tasks and minimize data loss.
  - Impact: Complexity in data synchronization.

- Latency: 10ms
  - Reason: To increase hardware buffer size.
  - Impact: Adds slight delay but improves data integrity.
"""

from time import sleep
import sounddevice as sd
import threading
import queue
from data_distubuter import DataDistributor
from wav_writer import WavWriter
from print_data import PrintData
SAMPLERATE = 384_000
CHANNELS = 1
LATENCY = 0.1
BLOCKSIZE = int(SAMPLERATE * LATENCY)

class NoMicrophoneException(Exception):
    pass

class AudioRecorder:
    def __init__(self):
        self.mic_num = self.select_mic()
        self.audio_queue = queue.Queue()

    def select_mic(self):
        mic_list = sd.query_devices()
        filtered_mic_list = [mic for mic in mic_list if mic['default_samplerate'] == SAMPLERATE]
        if len(filtered_mic_list) == 0:
            raise NoMicrophoneException("No microphone found.")
        # Selects the first microphone with the correct samplerate. Might be a problem in the future
        return filtered_mic_list[0]['index']


    def start(self):
        self.stop_recording = threading.Event()
        self.record_thread = threading.Thread(target=self.record_audio) 

        consumer_classes = [WavWriter]
        self.distributor = DataDistributor(consumer_classes, self.audio_queue, queue.Queue) 
        
        self.distributor.start()
        self.record_thread.start()

    def stop(self):
        self.stop_recording.set()
        self.distributor.stop()
        self.record_thread.join()

    def record_audio(self):
        try:
            with sd.InputStream(device=self.mic_num, channels=CHANNELS, samplerate=SAMPLERATE, latency=LATENCY, dtype='int16') as stream:
                while not self.stop_recording.is_set():
                    audio_chunk, overflowed = stream.read(BLOCKSIZE)
                    self.audio_queue.put(audio_chunk)
                    if overflowed:
                        print("Overflowed")
        except Exception as e:
            print(f"An error occurred: {e}")
