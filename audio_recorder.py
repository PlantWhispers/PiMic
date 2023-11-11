from time import sleep
import sounddevice as sd
import threading
import queue
from wav_writer import WavWriter

SAMPLERATE = 384_000
CHANNELS = 2
LATENCY = 0.1
BLOCKSIZE = int(SAMPLERATE * LATENCY)

class NoMicrophoneException(Exception):
    pass

class AudioRecorder:
    def __init__(self):
        self._mic_num = self._select_mic()
        self._audio_queue = queue.Queue()

    def _select_mic(self):
        mic_list = sd.query_devices()
        for mic in mic_list:
            if mic['name'] == 'PlantMic':
                return mic['index']

        raise NoMicrophoneException("No microphone found.")    


    def start(self):
        self._stop_recording = threading.Event()
        self._record_thread = threading.Thread(target=self._record_audio) 

        self._wav_writer = WavWriter(self._audio_queue, SAMPLERATE, CHANNELS)
        self._writer_thread = threading.Thread(target=self._wav_writer.run)

        
        self._record_thread.start()
        self._writer_thread.start()

    def stop(self):
        self._stop_recording.set()
        self._record_thread.join()
        self._wav_writer.stop()
        self._writer_thread.join()

    def _record_audio(self):
        try:
            num_blocks = 1
            with sd.InputStream(device=self._mic_num, channels=CHANNELS, samplerate=SAMPLERATE, latency=LATENCY, dtype='int16') as stream:
                while not self._stop_recording.is_set():
                    # BUG: Always overflows on the 4th block
                    audio_chunk, overflowed = stream.read(BLOCKSIZE)
                    self._audio_queue.put(audio_chunk)
                    num_blocks += 1
                    if overflowed:
                        print(f"\nOverflowed on block: {num_blocks}")
        except Exception as e:
            print(f"An error occurred: {e}")