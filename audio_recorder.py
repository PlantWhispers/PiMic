import sounddevice as sd
import numpy as np
import wavio
import threading
from datetime import datetime
import os

class AudioRecorder:
    def __init__(self, fs, channels):
        self.fs = fs
        self.channels = channels
        self.thread = None
        self.mic_num = self.initialize_mic()
        self.recording = np.empty((0, self.channels), dtype='int16')
        self.start_time = None

    def initialize_mic(self):
        devices = sd.query_devices()
        device_name = "UltraMic384K_EVO 16bit r0: USB Audio (hw:1,0)"
        mic_num = next((i for i, device in enumerate(devices) if device['name'] == device_name), None)
        if mic_num is None:
            print("Device not found. Available devices are:")
            for i, device in enumerate(devices):
                print(f"{i}: {device['name']}")
            exit(1)
        return mic_num

    def start(self):
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
            with sd.InputStream(device=self.mic_num, channels=self.channels, samplerate=self.fs, dtype='int16') as stream:
                print("Recording... Press Ctrl+C to stop.")
                while not self.stop_recording.is_set():
                    audio_chunk, overflowed = stream.read(self.fs)
                    self.recording = np.vstack((self.recording, audio_chunk))
        except KeyboardInterrupt:
            print("Stopped by user.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            return self.save_recording(self.recording, self.start_time)

    def save_recording(self, recording, start_time):
        if recording.size == 0:
            print("No audio data recorded.")
            return
        end_time = datetime.now()
        duration = end_time - start_time
        duration_str = f"{duration.seconds//3600}h{duration.seconds//60%60}m{duration.seconds%60}s"
        current_time = end_time.strftime("%Y-%m-%d--%H-%M-%S")
        filename = f"{duration_str}--{current_time}.wav"
        if not os.path.exists('recordings'):
            os.makedirs('recordings')
        final_path = os.path.join('recordings', filename)
        wavio.write(final_path, recording, self.fs, sampwidth=2)
        print(f"Done. Saved as {filename}")
        return filename
