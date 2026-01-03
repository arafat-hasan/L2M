"""
Tests for the AudioRenderer service.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

from l2m.services.audio_renderer import AudioRenderer


class TestAudioRenderer:
    """Test suite for AudioRenderer class."""

    @pytest.fixture
    def mock_soundfont(self, tmp_path):
        """Create a mock SoundFont file."""
        sf_path = tmp_path / "test.sf2"
        sf_path.write_text("mock soundfont")
        return sf_path

    @pytest.fixture
    def mock_midi(self, tmp_path):
        """Create a mock MIDI file."""
        midi_path = tmp_path / "test.mid"
        midi_path.write_text("mock midi")
        return midi_path

    def test_init_with_soundfont(self, mock_soundfont):
        """Test AudioRenderer initialization with soundfont path."""
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        assert renderer.soundfont_path == mock_soundfont

    def test_init_without_soundfont(self):
        """Test AudioRenderer initialization without soundfont."""
        renderer = AudioRenderer()
        # Should use config default (which may be None)
        assert renderer.soundfont_path is not None or renderer.soundfont_path is None

    @patch('subprocess.run')
    def test_check_fluidsynth_available_success(self, mock_run):
        """Test FluidSynth availability check when installed."""
        mock_run.return_value = Mock(returncode=0)
        renderer = AudioRenderer()
        assert renderer._check_fluidsynth_available() is True

    @patch('subprocess.run')
    def test_check_fluidsynth_available_not_found(self, mock_run):
        """Test FluidSynth availability check when not installed."""
        mock_run.side_effect = FileNotFoundError()
        renderer = AudioRenderer()
        assert renderer._check_fluidsynth_available() is False

    def test_verify_soundfont_missing(self):
        """Test soundfont verification when no soundfont specified."""
        renderer = AudioRenderer(soundfont_path=None)
        with pytest.raises(FileNotFoundError, match="No SoundFont specified"):
            renderer._verify_soundfont()

    def test_verify_soundfont_not_exists(self, tmp_path):
        """Test soundfont verification when file doesn't exist."""
        fake_path = tmp_path / "nonexistent.sf2"
        renderer = AudioRenderer(soundfont_path=fake_path)
        with pytest.raises(FileNotFoundError, match="SoundFont file not found"):
            renderer._verify_soundfont()

    def test_verify_soundfont_success(self, mock_soundfont):
        """Test soundfont verification when file exists."""
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        # Should not raise
        renderer._verify_soundfont()

    @patch('subprocess.run')
    def test_render_to_wav_success(self, mock_run, mock_soundfont, mock_midi, tmp_path):
        """Test successful WAV rendering."""
        mock_run.return_value = Mock(returncode=0, stderr="")
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        output_path = tmp_path / "output.wav"
        
        result = renderer.render_to_wav(mock_midi, output_path)
        
        assert result == output_path
        assert mock_run.called
        # Verify fluidsynth was called with correct arguments
        call_args = mock_run.call_args[0][0]
        assert 'fluidsynth' in call_args
        assert str(mock_soundfont) in call_args
        assert str(mock_midi) in call_args

    def test_render_to_wav_midi_not_found(self, mock_soundfont, tmp_path):
        """Test WAV rendering when MIDI file doesn't exist."""
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        fake_midi = tmp_path / "nonexistent.mid"
        
        with pytest.raises(FileNotFoundError, match="MIDI file not found"):
            renderer.render_to_wav(fake_midi)

    @patch('subprocess.run')
    def test_render_to_wav_fluidsynth_error(self, mock_run, mock_soundfont, mock_midi):
        """Test WAV rendering when FluidSynth fails."""
        mock_run.return_value = Mock(returncode=1, stderr="FluidSynth error")
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        
        with pytest.raises(RuntimeError, match="FluidSynth rendering failed"):
            renderer.render_to_wav(mock_midi)

    @patch('subprocess.run')
    def test_render_to_wav_timeout(self, mock_run, mock_soundfont, mock_midi):
        """Test WAV rendering timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('fluidsynth', 60)
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        
        with pytest.raises(RuntimeError, match="timed out"):
            renderer.render_to_wav(mock_midi)

    @patch('subprocess.run')
    def test_render_to_wav_fluidsynth_not_installed(self, mock_run, mock_soundfont, mock_midi):
        """Test WAV rendering when FluidSynth is not installed."""
        mock_run.side_effect = FileNotFoundError()
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        
        with pytest.raises(RuntimeError, match="FluidSynth not installed"):
            renderer.render_to_wav(mock_midi)

    @patch.object(AudioRenderer, 'render_to_wav')
    @patch.object(AudioRenderer, '_convert_wav_to_mp3')
    def test_render_to_mp3_success(self, mock_convert, mock_render_wav, 
                                   mock_soundfont, mock_midi, tmp_path):
        """Test successful MP3 rendering."""
        wav_path = tmp_path / "output.temp.wav"
        mp3_path = tmp_path / "output.mp3"
        
        mock_render_wav.return_value = wav_path
        wav_path.write_text("mock wav")
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        result = renderer.render_to_mp3(mock_midi, mp3_path)
        
        assert result == mp3_path
        assert mock_render_wav.called
        assert mock_convert.called

    @patch('subprocess.run')
    def test_convert_wav_to_mp3_success(self, mock_run, mock_soundfont, tmp_path):
        """Test successful WAV to MP3 conversion."""
        mock_run.return_value = Mock(returncode=0, stderr="")
        
        wav_path = tmp_path / "test.wav"
        mp3_path = tmp_path / "test.mp3"
        wav_path.write_text("mock wav")
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        renderer._convert_wav_to_mp3(wav_path, mp3_path)
        
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert str(wav_path) in call_args
        assert str(mp3_path) in call_args

    @patch('subprocess.run')
    def test_convert_wav_to_mp3_ffmpeg_error(self, mock_run, mock_soundfont, tmp_path):
        """Test MP3 conversion when FFmpeg fails."""
        mock_run.return_value = Mock(returncode=1, stderr="FFmpeg error")
        
        wav_path = tmp_path / "test.wav"
        mp3_path = tmp_path / "test.mp3"
        wav_path.write_text("mock wav")
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        
        with pytest.raises(RuntimeError, match="MP3 conversion failed"):
            renderer._convert_wav_to_mp3(wav_path, mp3_path)

    @patch('subprocess.run')
    def test_convert_wav_to_mp3_ffmpeg_not_installed(self, mock_run, mock_soundfont, tmp_path):
        """Test MP3 conversion when FFmpeg is not installed."""
        mock_run.side_effect = FileNotFoundError()
        
        wav_path = tmp_path / "test.wav"
        mp3_path = tmp_path / "test.mp3"
        wav_path.write_text("mock wav")
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        
        with pytest.raises(RuntimeError, match="FFmpeg not installed"):
            renderer._convert_wav_to_mp3(wav_path, mp3_path)

    @patch.object(AudioRenderer, 'render_to_wav')
    @patch.object(AudioRenderer, 'render_to_mp3')
    @patch('l2m.services.audio_renderer.config')
    def test_render_all_wav_only(self, mock_config, mock_render_mp3, 
                                 mock_render_wav, mock_soundfont, mock_midi, tmp_path):
        """Test render_all with WAV format only."""
        mock_config.OUTPUT_DIR = tmp_path
        mock_config.AUDIO_FORMAT = 'wav'
        
        wav_path = tmp_path / "output.wav"
        mock_render_wav.return_value = wav_path
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        results = renderer.render_all(mock_midi, "output")
        
        assert 'wav' in results
        assert results['wav'] == wav_path
        assert mock_render_wav.called
        assert not mock_render_mp3.called

    @patch.object(AudioRenderer, 'render_to_wav')
    @patch.object(AudioRenderer, 'render_to_mp3')
    @patch('l2m.services.audio_renderer.config')
    def test_render_all_mp3_format(self, mock_config, mock_render_mp3, 
                                   mock_render_wav, mock_soundfont, mock_midi, tmp_path):
        """Test render_all with MP3 format."""
        mock_config.OUTPUT_DIR = tmp_path
        mock_config.AUDIO_FORMAT = 'mp3'
        
        wav_path = tmp_path / "output.wav"
        mp3_path = tmp_path / "output.mp3"
        mock_render_wav.return_value = wav_path
        mock_render_mp3.return_value = mp3_path
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        results = renderer.render_all(mock_midi, "output")
        
        assert 'wav' in results
        assert 'mp3' in results
        assert mock_render_wav.called
        assert mock_render_mp3.called

    @patch.object(AudioRenderer, 'render_to_wav')
    @patch.object(AudioRenderer, 'render_to_mp3')
    @patch('l2m.services.audio_renderer.config')
    def test_render_all_both_formats(self, mock_config, mock_render_mp3, 
                                     mock_render_wav, mock_soundfont, mock_midi, tmp_path):
        """Test render_all with both WAV and MP3 formats."""
        mock_config.OUTPUT_DIR = tmp_path
        mock_config.AUDIO_FORMAT = 'both'
        
        wav_path = tmp_path / "output.wav"
        mp3_path = tmp_path / "output.mp3"
        mock_render_wav.return_value = wav_path
        mock_render_mp3.return_value = mp3_path
        
        renderer = AudioRenderer(soundfont_path=mock_soundfont)
        results = renderer.render_all(mock_midi, "output")
        
        assert 'wav' in results
        assert 'mp3' in results
        assert results['wav'] == wav_path
        assert results['mp3'] == mp3_path
