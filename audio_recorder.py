import sounddevice as sd
import numpy as np
import wavio
import threading
from datetime import datetime
import os
import struct
import shutil

SAMPLERATE = 384_000
CHANNELS = 1
TEMP_FILE_PATH = ".cache/temp.raw"

class AudioRecorder:
    def __init__(self):
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
        header = self.create_wav_header()
        with open(TEMP_FILE_PATH, "wb") as f:
            f.write(header)
        
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
            with sd.InputStream(device=self.mic_num, channels=CHANNELS, samplerate=SAMPLERATE, dtype='int16') as stream, open(TEMP_FILE_PATH, "ab") as f:
                while not self.stop_recording.is_set():
                    audio_chunk, overflowed = stream.read(SAMPLERATE)
                    self.num_samples += len(audio_chunk)
                    f.write(audio_chunk.tobytes())
                    if overflowed:
                        print("Overflowed")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.save_recording(self.start_time, self.num_samples)

    def save_recording(self, start_time, num_samples):

        self.update_wav_sizes()

        time_str = start_time.strftime("%m-%d--%H-%M-%S")
        filename = f"{time_str}.wav"
        if not os.path.exists('recordings'):
            os.makedirs('recordings')
        final_path = os.path.join('recordings', filename)

        shutil.move(TEMP_FILE_PATH, final_path)

        return filename

    def update_wav_sizes(self):
        with open(TEMP_FILE_PATH, "rb+") as f:
            # Seek to the end to get total file size
            f.seek(0, os.SEEK_END)
            total_file_size = f.tell()
            
            # Calculate ChunkSize and Subchunk2Size
            chunk_size = total_file_size - 8
            subchunk2_size = total_file_size - 44

            print(f"chunk_size:{chunk_size}\nsubchunk2_size:{subchunk2_size}")

            # Update ChunkSize (at byte position 4-7)
            f.seek(4)
            f.write(struct.pack('<I', chunk_size))
            
            # Update Subchunk2Size (at byte position 40-43)
            f.seek(40)
            f.write(struct.pack('<I', subchunk2_size))


    @staticmethod
    def create_wav_header(num_channels=CHANNELS, sample_width=2, sample_rate=SAMPLERATE):
        byte_rate = sample_rate * num_channels * sample_width
        print(f"byte_rate:{byte_rate}")
        block_align = num_channels * sample_width
        print(f"block_align:{block_align}")
        # subchunk2_size = num_samples * num_channels * sample_width
        # print(f"subchunk2_size:{subchunk2_size}")

        wav_header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            00,
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
            00,
        )
        
        print(wav_header)

        return wav_header
