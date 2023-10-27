import sounddevice as sd
import numpy as np
import wavio
import threading
from datetime import datetime
import os
import struct
import shutil

class AudioRecorder:
    def __init__(self, samplerate, channels):
        self.samplerate = samplerate
        self.channels = channels
        self.thread = None
        self.mic_num = None
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

        # Create temp file to offload memory
        if not os.path.exists('.cache'):
            os.makedirs('.cache')
        with open(".cache/temp.raw", "wb") as f:
            f.write(b"\x00" * 44)
        
        self.stop_recording = threading.Event()
        self.thread = threading.Thread(target=self.record_audio) 
        self.thread.start()

    def stop(self):
        self.stop_recording.set()
        self.thread.join()

    def record_audio(self):
        self.start_time = datetime.now()
        self.num_samples = 0
        try:
            with sd.InputStream(device=self.mic_num, channels=self.channels, samplerate=self.samplerate, dtype='int16') as stream, open(".cache/temp.raw", "ab") as f:
                while not self.stop_recording.is_set():
                    audio_chunk, overflowed = stream.read(self.samplerate)
                    self.num_samples += len(audio_chunk)
                    f.write(audio_chunk.tobytes())
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.save_recording(self.start_time, self.num_samples)

    def save_recording(self, start_time, num_samples):

        # Create WAV header
        header = self.create_wav_header(num_samples)
        with open(".cache/temp.raw", "r+b") as f:
            f.seek(0)
            f.write(header)

        time_str = start_time.strftime("%m-%d--%H-%M-%S")
        filename = f"{time_str}.wav"
        if not os.path.exists('recordings'):
            os.makedirs('recordings')
        final_path = os.path.join('recordings', filename)

        shutil.move(".cache/temp.raw", final_path)

        return filename


    @staticmethod
    def create_wav_header(num_samples, num_channels=1, sample_width=2, sample_rate=384_000):
        byte_rate = sample_rate * num_channels * sample_width
        block_align = num_channels * sample_width
        subchunk2_size = num_samples * num_channels * sample_width

        wav_header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + subchunk2_size,
            b"WAVE",
            b"fmt ",
            16,
            1,
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            sample_width * 8,
            b"data",
            subchunk2_size,
        )

        return wav_header
