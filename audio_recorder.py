import sounddevice as sd
import numpy as np
import wavio
import threading
from datetime import datetime
import os
import struct
import shutil
import queue

SAMPLERATE = 384_000
CHANNELS = 1
CACHE_FOLDER = ".cache"
TEMP_FILE_PATH = os.path.join(CACHE_FOLDER,"temp.raw")
LATENCY = 0.01
BLOCKSIZE = int(SAMPLERATE * LATENCY)

class NoMicrophoneException(Exception):
    pass

class AudioRecorder:
    def __init__(self):
        self.mic_num = self.select_mic()
        self.start_time = None
        self.audio_queue = queue.Queue()
        self.last_filename = None

    def select_mic(self):
        mic_list = sd.query_devices()
        filtered_mic_list = [mic for mic in mic_list if mic['default_samplerate'] == SAMPLERATE]
        if len(filtered_mic_list) == 0:
            raise NoMicrophoneException("No microphone found.")
        # Selects the first microphone with the correct samplerate. Might be a problem in the future
        return filtered_mic_list[0]['index']


    def start(self):
        # Create temp file to offload memory
        if not os.path.exists(CACHE_FOLDER):
            os.makedirs(CACHE_FOLDER)
        header = self.create_wav_header()
        with open(TEMP_FILE_PATH, "wb") as f:
            f.write(header)
        
        self.stop_recording = threading.Event()
        self.record_thread = threading.Thread(target=self.record_audio) 
        self.write_thread = threading.Thread(target=self.write_audio)
        self.record_thread.start()
        self.write_thread.start()

    def stop(self):
        self.stop_recording.set()
        self.record_thread.join()
        self.write_thread.join()
        return self.last_filename

    def record_audio(self):
        self.start_time = datetime.now()
        try:
            with sd.InputStream(device=self.mic_num, channels=CHANNELS, samplerate=SAMPLERATE, latency=LATENCY, dtype='int16') as stream:#, open(TEMP_FILE_PATH, "ab") as f:
                while not self.stop_recording.is_set():
                    audio_chunk, overflowed = stream.read(BLOCKSIZE)
                    self.audio_queue.put(audio_chunk)
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.save_recording(self.start_time)

    def write_audio(self):
        with open(TEMP_FILE_PATH, "ab") as f:
            while not self.stop_recording.is_set():
                audio_chunk = self.audio_queue.get()
                f.write(audio_chunk.tobytes())

    def save_recording(self, start_time):
        self.update_wav_sizes()

        time_str = start_time.strftime("%m-%d--%H-%M-%S")
        filename = f"{time_str}.wav"
        if not os.path.exists('recordings'):
            os.makedirs('recordings')
        final_path = os.path.join('recordings', filename)

        self.last_filename = final_path

        shutil.move(TEMP_FILE_PATH, final_path)

    def update_wav_sizes(self):
        with open(TEMP_FILE_PATH, "rb+") as f:
            # Seek to the end to get total file size
            f.seek(0, os.SEEK_END)
            total_file_size = f.tell()
            
            # Calculate ChunkSize and Subchunk2Size
            chunk_size = total_file_size - 8
            subchunk2_size = total_file_size - 44

            # Update ChunkSize (at byte position 4-7)
            f.seek(4)
            f.write(struct.pack('<I', chunk_size))
            
            # Update Subchunk2Size (at byte position 40-43)
            f.seek(40)
            f.write(struct.pack('<I', subchunk2_size))


    @staticmethod
    def create_wav_header(num_channels=CHANNELS, sample_width=2, sample_rate=SAMPLERATE):
        byte_rate = sample_rate * num_channels * sample_width
        block_align = num_channels * sample_width

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
        
        return wav_header
