#wav_writer.py
from datetime import datetime
import os
import struct
import shutil
from queue import Empty, Queue
import threading

# Constants from your audio_recorder.py, adjust as necessary
CACHE_FOLDER = ".cache"
RECORDINGS_FOLDER = "recordings"
TEMP_FILE_PATH = os.path.join(CACHE_FOLDER, "temp.raw")

class WavWriter():
    def __init__(self, queue: Queue, sample_rate: int, num_channels: int ):
        self._queue = queue
        self._stop_event = threading.Event()
        self._sample_rate = sample_rate
        self._num_channels = num_channels
        self._filename = f"{datetime.now().strftime('%m-%d--%H-%M-%S')}.wav"
        os.makedirs(CACHE_FOLDER, exist_ok=True)
        os.makedirs(RECORDINGS_FOLDER, exist_ok=True)

    def _create_wav_header(self, sample_width=2):
        byte_rate = self._sample_rate * self._num_channels * sample_width
        block_align = self._num_channels * sample_width

        wav_header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            0,  # Placeholder for file size
            b"WAVE",
            b"fmt ",
            16,
            1,
            self._num_channels,
            self._sample_rate,
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
            temp_file.write(self._create_wav_header())
            while not self._stop_event.is_set() or not self._queue.empty():
                try:
                    audio_chunk = self._queue.get(timeout=1)
                except Empty:
                    continue
                temp_file.write(audio_chunk.tobytes())
                #print("Writing")

            #print("Finished writing")
            # Update the WAV header with the correct file size information
            self._update_wav_header(temp_file)

        # Move the temporary file to the recordings directory with the appropriate filename
        shutil.move(TEMP_FILE_PATH, os.path.join(RECORDINGS_FOLDER, self._filename))

    def _update_wav_header(self, file):
        file.seek(0, os.SEEK_END)
        file_size = file.tell()

        chunk_size = file_size - 8
        subchunk2_size = file_size - 44

        file.seek(4)
        file.write(struct.pack('<I', chunk_size))

        file.seek(40)
        file.write(struct.pack('<I', subchunk2_size))

    def stop(self):
        self._stop_event.set()