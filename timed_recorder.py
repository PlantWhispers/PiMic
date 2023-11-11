import time
import sys
import re
from audio_recorder import AudioRecorder


def _parse_duration(duration_str):
    # Match the duration string with regex
    pattern = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
    parts = pattern.match(duration_str)
    if not parts:
        return None
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)
    return time_params


def _convert_to_seconds(hours, minutes, seconds):
    return hours * 3600 + minutes * 60 + seconds


def _format_time(seconds):
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"
    else:
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"


def _progress_bar(duration):
    # Define progress bar parameters
    progress_length = 30
    full_char = '▓'
    empty_char = '░'
    start_time = time.time()

    # Update progress bar until duration is reached
    while True:
        elapsed_time = int(time.time() - start_time)
        if elapsed_time > duration:
            elapsed_time = duration
        elapsed_time_formatted = _format_time(elapsed_time)
        total_time_formatted = _format_time(duration)
        progress = int((elapsed_time / duration) * progress_length)
        progress_bar = full_char * progress + empty_char * (progress_length - progress)
        sys.stdout.write(f'\r{progress_bar} {elapsed_time_formatted}/{total_time_formatted}')
        sys.stdout.flush()
        if elapsed_time >= duration:
            break
        time.sleep(1)

    # Add newline after completion
    print()


if __name__ == "__main__":
    # Check for correct usage
    if len(sys.argv) != 2:
        print("Usage: python timed_recorder.py <duration>")
        print("Duration format: [Nh][Nm][Ns]")
        sys.exit(1)

    # Parse duration string
    duration_str = sys.argv[1]
    time_params = _parse_duration(duration_str)
    if time_params is None:
        print("Invalid duration format.")
        sys.exit(1)

    # Set default values if any time unit is missing
    hours = time_params.get('hours', 0)
    minutes = time_params.get('minutes', 0)
    seconds = time_params.get('seconds', 0)
    total_seconds = _convert_to_seconds(hours, minutes, seconds)

    # Start audio recording and progress bar
    recorder = AudioRecorder()
    recorder.start()
    try:
        _progress_bar(total_seconds)
    finally:
        recorder.stop()