"""
Audio rendering service.

Converts MIDI files to audio formats (WAV, MP3) using FluidSynth.
"""

import subprocess
from pathlib import Path
from typing import Optional

from l2m.config import config
from l2m.utils.logger import get_logger

logger = get_logger(__name__)


class AudioRenderer:
    """
    Service for rendering MIDI files to audio formats.

    Uses FluidSynth for high-quality MIDI synthesis.
    """

    def __init__(self, soundfont_path: Optional[Path] = None):
        """
        Initialize audio renderer.

        Args:
            soundfont_path: Path to SoundFont (.sf2) file. If None, uses config default.
        """
        self.soundfont_path = soundfont_path or config.SOUNDFONT_PATH
        logger.debug(f"[AudioRenderer] Initialized with soundfont: {self.soundfont_path}")

        # Verify FluidSynth is available
        if not self._check_fluidsynth_available():
            logger.warning(
                "[AudioRenderer] FluidSynth not found. "
                "Install with: brew install fluid-synth (macOS) or apt-get install fluidsynth (Linux)"
            )

    def _check_fluidsynth_available(self) -> bool:
        """
        Check if FluidSynth is installed and available.

        Returns:
            bool: True if FluidSynth is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['fluidsynth', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _verify_soundfont(self) -> None:
        """
        Verify that the SoundFont file exists.

        Raises:
            FileNotFoundError: If SoundFont file is not found
        """
        if not self.soundfont_path:
            raise FileNotFoundError(
                "No SoundFont specified. Please provide a SoundFont path via:\n"
                "  1. --soundfont CLI argument\n"
                "  2. SOUNDFONT_PATH in .env\n"
                "  3. Download a free SoundFont from: "
                "https://schristiancollins.com/generaluser.php"
            )

        if not self.soundfont_path.exists():
            raise FileNotFoundError(
                f"SoundFont file not found: {self.soundfont_path}\n"
                f"Please ensure the file exists or download a SoundFont from:\n"
                f"https://schristiancollins.com/generaluser.php"
            )

    def render_to_wav(
        self,
        midi_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Render MIDI file to WAV audio.

        Args:
            midi_path: Path to input MIDI file
            output_path: Optional output path. If None, uses same name as MIDI with .wav

        Returns:
            Path: Path to generated WAV file

        Raises:
            FileNotFoundError: If MIDI file or SoundFont not found
            RuntimeError: If FluidSynth rendering fails
        """
        # Verify inputs
        if not midi_path.exists():
            raise FileNotFoundError(f"MIDI file not found: {midi_path}")

        self._verify_soundfont()

        # Determine output path
        if output_path is None:
            output_path = midi_path.with_suffix('.wav')

        logger.info(f"[AudioRenderer] Rendering MIDI to WAV: {midi_path} -> {output_path}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)


        # Build FluidSynth command
        # FluidSynth v2.5+ requires output flags BEFORE soundfont and MIDI files
        # -ni: non-interactive mode
        # -F: output to file
        # -r: sample rate
        # -g: gain (volume)
        command = [
            'fluidsynth',
            '-ni',                               # Non-interactive
            '-F', str(output_path),              # Output file (must come before SF2/MIDI)
            '-r', str(config.AUDIO_SAMPLE_RATE), # Sample rate
            '-g', '1.0',                         # Gain
            str(self.soundfont_path),            # SoundFont file
            str(midi_path)                       # Input MIDI
        ]


        try:
            logger.debug(f"[AudioRenderer] Running command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"[AudioRenderer] FluidSynth error: {result.stderr}")
                raise RuntimeError(
                    f"FluidSynth rendering failed with code {result.returncode}\n"
                    f"Error: {result.stderr}"
                )

            logger.info(f"[AudioRenderer] Successfully rendered WAV: {output_path}")
            return output_path

        except subprocess.TimeoutExpired:
            logger.error("[AudioRenderer] FluidSynth timeout")
            raise RuntimeError("Audio rendering timed out after 60 seconds")
        except FileNotFoundError:
            logger.error("[AudioRenderer] FluidSynth not found")
            raise RuntimeError(
                "FluidSynth not installed. Install with:\n"
                "  macOS: brew install fluid-synth\n"
                "  Linux: sudo apt-get install fluidsynth"
            )

    def render_to_mp3(
        self,
        midi_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Render MIDI file to MP3 audio.

        First renders to WAV, then converts to MP3 using FFmpeg.

        Args:
            midi_path: Path to input MIDI file
            output_path: Optional output path. If None, uses same name as MIDI with .mp3

        Returns:
            Path: Path to generated MP3 file

        Raises:
            FileNotFoundError: If MIDI file or SoundFont not found
            RuntimeError: If rendering or conversion fails
        """
        # Determine output path
        if output_path is None:
            output_path = midi_path.with_suffix('.mp3')

        logger.info(f"[AudioRenderer] Rendering MIDI to MP3: {midi_path} -> {output_path}")

        # First render to WAV (temporary file)
        temp_wav = output_path.with_suffix('.temp.wav')
        try:
            self.render_to_wav(midi_path, temp_wav)

            # Convert WAV to MP3 using FFmpeg
            self._convert_wav_to_mp3(temp_wav, output_path)

            logger.info(f"[AudioRenderer] Successfully rendered MP3: {output_path}")
            return output_path

        finally:
            # Clean up temporary WAV file
            if temp_wav.exists():
                temp_wav.unlink()
                logger.debug(f"[AudioRenderer] Cleaned up temp file: {temp_wav}")

    def _convert_wav_to_mp3(self, wav_path: Path, mp3_path: Path) -> None:
        """
        Convert WAV to MP3 using FFmpeg.

        Args:
            wav_path: Input WAV file
            mp3_path: Output MP3 file

        Raises:
            RuntimeError: If FFmpeg is not available or conversion fails
        """
        logger.debug(f"[AudioRenderer] Converting WAV to MP3: {wav_path} -> {mp3_path}")

        command = [
            'ffmpeg',
            '-i', str(wav_path),        # Input
            '-codec:a', 'libmp3lame',   # MP3 codec
            '-qscale:a', '2',           # Quality (0-9, 2 is high quality)
            '-y',                       # Overwrite output
            str(mp3_path)
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"[AudioRenderer] FFmpeg error: {result.stderr}")
                raise RuntimeError(
                    f"MP3 conversion failed with code {result.returncode}\n"
                    f"Error: {result.stderr}"
                )

        except FileNotFoundError:
            logger.error("[AudioRenderer] FFmpeg not found")
            raise RuntimeError(
                "FFmpeg not installed. Install with:\n"
                "  macOS: brew install ffmpeg\n"
                "  Linux: sudo apt-get install ffmpeg"
            )
        except subprocess.TimeoutExpired:
            logger.error("[AudioRenderer] FFmpeg timeout")
            raise RuntimeError("MP3 conversion timed out after 30 seconds")

    def render_all(
        self,
        midi_path: Path,
        output_name: str
    ) -> dict[str, Path]:
        """
        Render MIDI to all configured audio formats.

        Args:
            midi_path: Path to input MIDI file
            output_name: Base name for output files (without extension)

        Returns:
            dict: Mapping of format name to output path
                  e.g., {'wav': Path('output.wav'), 'mp3': Path('output.mp3')}
        """
        logger.info(f"[AudioRenderer] Rendering all formats for: {output_name}")

        output_dir = config.OUTPUT_DIR
        results = {}

        # Always render WAV
        wav_path = output_dir / f"{output_name}.wav"
        results['wav'] = self.render_to_wav(midi_path, wav_path)

        # Optionally render MP3 based on config
        if config.AUDIO_FORMAT == 'mp3' or config.AUDIO_FORMAT == 'both':
            mp3_path = output_dir / f"{output_name}.mp3"
            results['mp3'] = self.render_to_mp3(midi_path, mp3_path)

        logger.info(f"[AudioRenderer] Rendered {len(results)} audio format(s)")
        return results
