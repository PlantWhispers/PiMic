from datetime import datetime
import os
import struct
import shutil
from queue import Queue
from consumer_interface import ConsumerInterface

# Constants from your audio_recorder.py, adjust as necessary
SAMPLERATE = 384_000
CHANNELS = 1
CACHE_FOLDER = ".cache"
RECORDINGS_FOLDER = "recordings"
TEMP_FILE_PATH = os.path.join(CACHE_FOLDER, "temp.raw")

class WavWriter(ConsumerInterface):
    def __init__(self, queue: Queue):
        super().__init__(queue)
        self.filename = f"{datetime.now().strftime('%m-%d--%H-%M-%S')}.wav"
        os.makedirs(CACHE_FOLDER, exist_ok=True)
        os.makedirs(RECORDINGS_FOLDER, exist_ok=True)

    @staticmethod
    def create_wav_header(num_channels=CHANNELS, sample_width=2, sample_rate=SAMPLERATE):
        byte_rate = sample_rate * num_channels * sample_width
        block_align = num_channels * sample_width

        wav_header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            0,  # Placeholder for file size
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
            0,  # Placeholder for data chunk size
        )
        
        return wav_header

    def run (self):
        """
        Write the audio data to a temporary file and then move it to the recordings folder.
        """
        with open(TEMP_FILE_PATH, "wb+") as temp_file:
            temp_file.write(self.create_wav_header())
            while not self._stop_event.is_set() or not self.queue.empty():
                audio_chunk = self.queue.get()
                temp_file.write(audio_chunk.tobytes())

            # Update the WAV header with the correct file size information
            self.update_wav_header(temp_file)

        # Move the temporary file to the recordings directory with the appropriate filename
        shutil.move(TEMP_FILE_PATH, os.path.join(RECORDINGS_FOLDER, self.filename))

    def update_wav_header(self, file):
        file.seek(0, os.SEEK_END)
        file_size = file.tell()

        chunk_size = file_size - 8
        subchunk2_size = file_size - 44

        file.seek(4)
        file.write(struct.pack('<I', chunk_size))

        file.seek(40)
        file.write(struct.pack('<I', subchunk2_size))