# SoundFont Files

This directory contains SoundFont (`.sf2`) files used for MIDI-to-audio rendering.

## What are SoundFonts?

SoundFonts are collections of audio samples that define how MIDI instruments should sound. They're essential for converting MIDI files to realistic audio.

## Getting a SoundFont

### Recommended Free SoundFonts

1. **GeneralUser GS** (Recommended)
   - High quality, comprehensive instrument set
   - Size: ~30 MB
   - Download: https://schristiancollins.com/generaluser.php
   - Direct link: http://www.schristiancollins.com/soundfonts/GeneralUser_GS_1.471.zip

2. **FluidR3_GM**
   - Good quality, widely used
   - Size: ~140 MB
   - Download: https://member.keymusician.com/Member/FluidR3_GM/index.html

3. **Timbres of Heaven**
   - Excellent quality, large file
   - Size: ~350 MB
   - Download: http://midkar.com/soundfonts/

## Installation

1. Download a SoundFont file (`.sf2`)
2. Place it in this directory: `l2m/assets/soundfonts/`
3. Configure in one of two ways:

   **Option A: Environment variable (`.env` file)**
   ```bash
   SOUNDFONT_PATH=/Users/arafat/Work/github_personal/L2M/l2m/assets/soundfonts/GeneralUser_GS.sf2
   ```

   **Option B: CLI argument**
   ```bash
   python run.py --lyrics "Hello world" --audio --soundfont l2m/assets/soundfonts/GeneralUser_GS.sf2
   ```

## Quick Setup

```bash
# Download GeneralUser GS (recommended)
cd l2m/assets/soundfonts/
curl -L -O http://www.schristiancollins.com/soundfonts/GeneralUser_GS_1.471.zip
unzip GeneralUser_GS_1.471.zip
rm GeneralUser_GS_1.471.zip

# Add to .env
echo "SOUNDFONT_PATH=l2m/assets/soundfonts/GeneralUser_GS_1.471/GeneralUser_GS_v1.471.sf2" >> .env
```

## Usage

Once configured, audio rendering will automatically use the specified SoundFont:

```bash
# Generate MIDI + Audio
python run.py --lyrics "The sun will rise again" --audio
```

## Troubleshooting

**Error: "No SoundFont specified"**
- Make sure you've set `SOUNDFONT_PATH` in `.env` or use `--soundfont` flag

**Error: "SoundFont file not found"**
- Verify the file path is correct
- Check that the `.sf2` file exists in this directory

**Poor audio quality**
- Try a different SoundFont (GeneralUser GS is recommended)
- Ensure you're using a `.sf2` file, not other formats
