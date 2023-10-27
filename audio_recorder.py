import sounddevice as sd
import numpy as np
import wavio
import threading
from datetime import datetime
import os

class AudioRecorder:
    def __init__(self, samplerate, channels):
        self.samplerate = samplerate
        self.channels = channels
        self.thread = None
        # TODO
        self.mic_num = None
        self.recording = np.empty((0, self.channels), dtype='int16')
        self.start_time = None

    def get_mic_list(self):
        return sd.query_devices()
        
    def set_mic(self, mic_num):
        self.mic_num = mic_num

    class NoMicrophoneException(Exception):
        pass

    def start(self):
        if self.mic_num is None:
            raise NoMicrophoneException("No microphone selected.")
        self.stop_recording = threading.Event()
        self.thread = threading.Thread(target=self.record_audio)
        self.thread.start()

    def stop(self):
        self.stop_recording.set()
        self.thread.join()
        return self.save_recording(self.recording, self.start_time)

    def record_audio(self):
        self.recording = np.empty((0, self.channels), dtype='int16')
        self.start_time = datetime.now()
        try:
            with sd.InputStream(device=self.mic_num, channels=self.channels, samplerate=self.samplerate, dtype='int16') as stream:
                print("Recording... Press Ctrl+C to stop.")
                while not self.stop_recording.is_set():
                    audio_chunk, overflowed = stream.read(self.samplerate)
                    self.recording = np.vstack((self.recording, audio_chunk))
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            return self.save_recording(self.recording, self.start_time)

    def save_recording(self, recording, start_time):
        if recording.size == 0:
            print("No audio data recorded.")
            return
        end_time = datetime.now().strftime("%m-%d--%H-%M-%S")
        filename = f"{end_time}.wav"
        if not os.path.exists('recordings'):
            os.makedirs('recordings')
        final_path = os.path.join('recordings', filename)
        wavio.write(final_path, recording, self.samplerate, sampwidth=2)
        print(f"Done. Saved as {filename}")
        return filename
