import subprocess
import json
import os
from pathlib import Path
import logging

def transcode_video(input_file, output_file):
    """
    Transcode video using HandBrakeCLI with specified preset
    Args:
        input_file (str): Path to input video file
        output_file (str): Path to output video file
    Returns:
        bool: True if transcoding successful, False otherwise
    """
    try:
        input_path = Path(input_file)
        
        # Debug information
        logging.info(f"Input file: {input_path}")
        logging.info(f"Output file: {output_file}")
        
        # Verify input file exists and has size
        if not input_path.exists():
            logging.error(f"Input file does not exist: {input_file}")
            return False
        
        if input_path.stat().st_size == 0:
            logging.error(f"Input file is empty: {input_file}")
            return False
        
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        preset_path = project_root / 'presets' / 'CPU_Encode.json'
        
        if not preset_path.exists():
            logging.error(f"Preset file not found: {preset_path}")
            return False

        # Build HandBrakeCLI command
        cmd = [
            'HandBrakeCLI',
            '--input', str(input_file),
            '--output', str(output_file),
            '--preset-import-file', str(preset_path),
            '--preset', 'CPU_AV1',
            '--format', 'av_mkv',
            '--markers',
            '--optimize',
            '--all-audio',
            '--all-subtitles'
        ]

        logging.info(f"Starting transcode of: {input_path.name}")
        logging.info(f"Command: {' '.join(cmd)}")
        
        # Run HandBrakeCLI
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        # Print output in real-time
        for line in process.stdout:
            print(line, end='')

        process.wait()
        
        if process.returncode != 0:
            logging.error(f"HandBrake failed with return code: {process.returncode}")
            return False
            
        logging.info(f"Successfully transcoded: {input_path.name}")
        return True

    except Exception as e:
        logging.error(f"Error transcoding: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        success = transcode_video(sys.argv[1], sys.argv[2])
        print(f"Transcoding {'succeeded' if success else 'failed'}")
    else:
        print("Usage: python handbrake.py <input_file> <output_file>")
        print("Example: python handbrake.py '/path/to/input.mov' '/path/to/output.mkv'")
