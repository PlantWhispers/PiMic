# PiMic 🎙️
## Overview
PiMic is a Python-based audio recording application designed to capture high-frequency sounds emitted by plants under stress. It's part of the larger "PlantWhispers" research initiative. The program is optimized for running on a Raspberry Pi and uses a sampling rate of 384kHz.

## ⚠️ Development Warning
This project is under active development. Features may be incomplete or change without notice.

## Features
- Real-time audio recording at 384kHz
- Multi-threading for optimized performance
- Saving data firectly to storage storage to offload memory 
- Final audio saved in WAV format
- Designed to run on a Raspberry Pi

## Installation
1. Clone the repository
```bash
git clone https://github.com/PlantWhispers/PiMic.git
```
2. Navigate to the project directory
```bash
cd PiMic
```
3. Create a virtual environment
```bash
python3 -m venv .venv
```
4. Activate the virtual environment
```bash
source .venv/bin/activate # Linux
```
5. Install the requirements
```bash
pip install -r requirements.txt
```
## Usage
Run the audio_recorder.py script to launch the application.
```bash
python audio_recorder.py
```
## Contributing
Feel free to open issues or PRs for suggestions or bug-fixes.

## License
MIT License