# L2M: An LLM-Driven Lyrics-to-Melody Generation System with Emotion-Aware Alignment

---

## Abstract

We present **L2M**, a lyrics-to-melody generation system that leverages Large Language Models (LLMs) as the core reasoning engine for cross-modal music composition. Unlike prior approaches that require task-specific training on paired lyrics-melody corpora, L2M adopts a zero-shot prompting strategy: it first applies an LLM to classify the emotional content, tempo, and phrase structure of input lyrics, then uses a second LLM call to generate a syllable-aligned note sequence conditioned on the extracted musical attributes. A deterministic fallback mechanism based on emotion-to-key mappings and melodic contour heuristics ensures 100% operational reliability independent of API availability. The system produces standard music notation outputs (MIDI, MusicXML) and optional audio synthesis (WAV/MP3). Evaluation on a 20-sample benchmark spanning six emotion categories shows 100% syllable-note alignment accuracy, 95% emotion-key consistency, and 100% MIDI validity, with an average end-to-end latency of 3.2 seconds. L2M is released as an open-source Python package with a CLI and programmatic API, providing an accessible baseline for LLM-based music generation research.

**Keywords:** Lyrics-to-Melody Generation, Large Language Models, Prompt Engineering, Emotion-Aware Music Generation, Music Information Retrieval, Cross-Modal Generation

---

## 1. Introduction

### 1.1 Motivation

Music composition at the intersection of language and music requires simultaneous understanding of semantic meaning, emotional intent, syllabic rhythm, and musical structure. The task of **lyrics-to-melody (L2M) generation** — producing a singable melodic sequence from lyrical text — is particularly demanding because it requires:

1. **Semantic understanding** of lyrical content and emotional register
2. **Syllabic alignment** between phonetic units and individual musical notes
3. **Musical coherence** in terms of key, tempo, mode, and melodic contour
4. **Emotional consistency** between textual sentiment and musical expression

Traditional rule-based approaches lack the flexibility to handle the richness of natural language, while supervised deep learning approaches (Seq2Seq, Transformer-based) require large paired lyrics-melody datasets that are difficult and expensive to curate. The emergence of Large Language Models trained on vast corpora—including music theory texts, song analysis, and transcribed lyrics—opens a compelling alternative: can the emergent reasoning capabilities of LLMs be applied zero-shot to generate musically coherent melodies from lyrics?

### 1.2 Problem Statement

This work develops an **end-to-end system** that:

- Accepts arbitrary lyrical text as input with no prior training on lyrics-melody pairs
- Analyzes emotional content and rhythmic structure using LLM reasoning
- Generates musically coherent melodies with exact syllabic alignment
- Exports results in standard music notation formats (MIDI, MusicXML)
- Maintains robust operation via deterministic fallback heuristics when LLM calls fail

### 1.3 Contributions

This paper makes the following contributions:

1. **Two-Stage LLM Pipeline**: A novel decomposition of the lyrics-to-melody task into (a) emotion and rhythm analysis and (b) conditioned melody generation, each handled by separate LLM calls with structured JSON output schemas — enabling interpretability and targeted fallback at each stage.

2. **Emotion-Aware Alignment**: An explicit mapping from detected emotion categories to musical keys, tempo ranges, and melodic contour patterns, grounding LLM-generated output in music theory principles.

3. **Hybrid Reliability Architecture**: Combination of zero-shot LLM generation with deterministic heuristic fallbacks, achieving 100% system reliability across all tested inputs.

4. **Prompt Engineering Methodology**: Structured few-shot prompts with explicit output schemas, constraint enforcement ("EXACTLY N notes for N syllables"), and contextual carryover across long-lyric chunks — providing a reusable template for other cross-modal LLM tasks.

5. **Open-Source Baseline**: A production-ready Python package with CLI, programmatic API, multi-format output, and comprehensive logging — providing a reproducible baseline for the research community.

### 1.4 Paper Organization

Section 2 reviews related work. Section 3 describes the system architecture. Section 4 details the methodology, including prompt design and fallback strategy. Section 5 presents evaluation results. Section 6 discusses findings and limitations. Section 7 concludes with future directions.

---

## 2. Related Work

### 2.1 Generative Models for Music Composition

Deep learning approaches to symbolic music generation have employed LSTM, GAN, VAE, and Transformer architectures to model hierarchical temporal structures in music [1]. These foundational methods capture sequential dependencies and latent musical representations, forming the algorithmic basis for lyric-conditioned systems.

### 2.2 Lyrics-to-Melody Generation

**Neural Melody Composition from Lyrics** [2] introduced one of the earliest Seq2Seq neural frameworks for joint lyrics-melody generation using syllable-level alignment on pop music corpora. This work demonstrated feasibility but required large paired datasets.

**ReLyMe** [3] improved generation quality by explicitly incorporating music theory constraints (tonal relationships, rhythmic patterns) during decoding, addressing a core weakness of purely data-driven models: semantic and musical coherence.

**Controllable Lyrics-to-Melody Generation** [4] introduced style modulation via reference embeddings and memory fusion, enabling user-directed genre and mood control. This represents the shift from pure generation toward interactive music creation.

**SongComposer** [5] proposed a fine-tuned LLM that generates lyrics and melodies jointly, trained on large paired song datasets. While achieving high quality, this approach requires extensive domain-specific fine-tuning — a requirement our system eliminates via zero-shot prompting.

**Attention-based alignment networks** [6] address incomplete or partial lyric inputs by applying cross-attention between text and melody sequences, improving robustness in real-world scenarios.

**Contrastive melody-lyrics alignment** [7] uses self-supervised contrastive learning to build shared embedding spaces across modalities, demonstrating the importance of strong cross-modal representations for both generation and retrieval tasks.

### 2.3 Text-to-Music and Broader Multimodal Generation

Recent comprehensive reviews of AI-enabled text-to-music generation [8] classify systems along symbolic vs. audio synthesis axes and identify persistent challenges: long-term coherence, data scarcity, and limited expressiveness beyond simple harmonic structures. Systems like MusicLM and AudioCraft demonstrate powerful audio generation from text descriptions, but differ from our task in that they do not enforce syllabic alignment with lyrical text.

Transformer-based lyric generation approaches [9] have applied models such as T5 with contrastive decoding for lyric text creation, while LSTM-based approaches [10] established baselines for sequential lyric modeling.

### 2.4 Research Gap

Existing lyrics-to-melody systems share one or more of the following limitations:

| Limitation | Prevalence |
|---|---|
| Require large paired lyrics-melody training corpora | Most neural systems |
| No graceful degradation when model fails | Most systems |
| Single output format (MIDI only) | Most systems |
| No explicit emotion-to-key grounding | Many systems |
| Not available as deployable software | Most research systems |

**Our approach** directly addresses all five gaps through zero-shot LLM prompting, deterministic fallbacks, multi-format output, explicit emotion-music mappings, and open-source deployment.

---

## 3. System Architecture

### 3.1 Pipeline Overview

L2M follows a **six-stage sequential pipeline** where each stage produces a validated, typed output consumed by the next:

```
Lyrics Input
    │
    ▼
[Stage 1] Lyrics Parsing
    │  Normalized text + phrase structure
    ▼
[Stage 2] Emotion & Rhythm Analysis  ←── LLM Call 1
    │  EmotionAnalysis {emotion, tempo, time_sig, phrases[]}
    ▼
[Stage 3] Melody Structure Generation  ←── LLM Call 2
    │  MelodyStructure {key, melody[{note, duration, velocity}]}
    ▼
[Stage 4] Internal Representation Building
    │  Melody IR {NoteEvent[], tempo, time_sig}
    ▼
[Stage 5] MIDI / MusicXML Export
    │  .mid + .musicxml files
    ▼
[Stage 6] Audio Rendering (Optional)
       .wav / .mp3 files
```

**Figure 1: L2M System Pipeline**

At each LLM-dependent stage (2 and 3), a fallback path activates automatically on API failure, timeout, or malformed response, ensuring the pipeline always produces output.

### 3.2 Design Principles

| Principle | Realization |
|---|---|
| **Modularity** | Each stage is an independent service with defined input/output types |
| **Type Safety** | Pydantic v2 models validate every inter-stage data structure |
| **Robustness** | Fallback heuristics at Stages 2 and 3 ensure 100% completion rate |
| **Observability** | Structured logging with component-level context at every stage |
| **Extensibility** | Service interfaces allow drop-in replacement (e.g., different LLM provider, different audio synthesizer) |

### 3.3 Data Flow Types

```
str (raw lyrics)
  → NormalizedLyrics (str + phrase list)
  → EmotionAnalysis (Pydantic model)
  → MelodyStructure (Pydantic model)
  → Melody IR (dataclass)
  → music21.stream.Stream
  → MIDI / MusicXML / WAV / MP3 files
```

Each transition is guarded by Pydantic validation, catching malformed LLM outputs before they propagate downstream.

---

## 4. Methodology

### 4.1 Stage 1: Lyrics Parsing

The `LyricParser` service performs text preprocessing:
- **Normalization**: Collapse whitespace, strip excess punctuation, handle line breaks
- **Phrase segmentation**: Split on newlines and sentence boundaries into lyric phrases
- **Syllable estimation**: Vowel-cluster counting with adjustments for silent 'e' endings, providing an approximate syllable count per phrase

Syllable estimation serves as a reference for the LLM (which computes its own count) and for fallback melody generation.

### 4.2 Stage 2: Emotion and Rhythm Analysis via LLM

The first LLM call uses a structured few-shot prompt to extract:

| Field | Type | Description |
|---|---|---|
| `emotion` | string | Dominant emotion: *happy, sad, hopeful, tense, calm, excited, melancholic* |
| `tempo` | int | Suggested BPM (validated range: 40–200) |
| `time_signature` | string | e.g., `4/4`, `3/4`, `6/8` |
| `phrases` | list | Per-line syllable breakdowns: `[{line, syllables}]` |

**Prompt Structure:**
1. System role assignment ("expert music composer and emotional analyst")
2. JSON output schema specification
3. Three diverse few-shot examples (happy, sad, hopeful)
4. Empirically-derived tempo range guidelines per emotion category
5. Target lyrics insertion point
6. Format enforcement instruction

**Fallback (Stage 2):** If the LLM call fails or returns invalid JSON, a keyword-matching heuristic detects emotion from a curated lexicon (e.g., "rain", "fade", "dark" → *sad*; "dance", "shine", "joy" → *happy*), and assigns the median tempo and common time signature for that emotion category.

### 4.3 Stage 3: Melody Structure Generation via LLM

The second LLM call generates a syllable-aligned note sequence conditioned on the emotion analysis. The prompt receives: detected emotion, BPM, time signature, total syllable count, and the lyrics.

**Key Prompt Constraints:**
- Emotion-to-key mapping guides key selection (e.g., positive emotions → major keys; negative/tense → minor keys)
- **Hard constraint**: "Generate EXACTLY {N} notes — one per syllable"
- Vocal range constraint: C3–C5 (scientifically notated)
- Duration value set: {0.25, 0.5, 1.0, 2.0, 4.0} beats
- Contour guidance: "avoid large melodic jumps; create natural phrase arcs"

**Chunking for Long Lyrics:** When total syllables exceed a configurable threshold (default: 30), the system splits lyrics into phrase-level chunks and issues sequential LLM calls, carrying the last three notes of each chunk as context for the next to maintain melodic continuity.

**Fallback (Stage 3):** A deterministic melody generator uses the emotion-to-musical-attribute mapping table below and algorithmically constructs a note sequence following the specified contour pattern:

| Emotion | Key | Tempo Range (BPM) | Melodic Contour |
|---|---|---|---|
| Happy | C major | 100–120 | Ascending |
| Hopeful | G major | 80–100 | Wavy (arch) |
| Sad | A minor | 60–80 | Descending |
| Tense | D minor | 90–110 | Erratic (high variance) |
| Calm | F major | 60–80 | Balanced (small intervals) |
| Excited | D major | 120–140 | Ascending (steep) |

**Table 1: Emotion-to-Musical Attribute Mapping**

Contour algorithms:
- **Ascending/Descending**: Monotonic pitch progression with occasional plateaus based on syllable stress
- **Wavy**: Alternating up/down movement within a ±5 semitone range
- **Balanced**: Gaussian-weighted note selection centered on the tonic
- **Erratic**: Uniform random jumps within scale degrees for tension

### 4.4 Stage 4: Internal Representation

`MelodyGenerator.build_melody_ir()` converts the Pydantic `MelodyStructure` into a typed `Melody` dataclass comprising:
- `NoteEvent[]`: scientific pitch notation + duration (quarter-note units) + MIDI velocity
- `tempo`: int (BPM)
- `time_signature`: string
- `key`: string

Note validation enforces pitch range bounds and duration positivity before this stage completes.

### 4.5 Stage 5: MIDI/MusicXML Export

The `MIDIWriter` service converts the `Melody` IR to a `music21.stream.Stream`, adding:
- Tempo marking (`MetronomeMark`)
- Key signature (`KeySignature`)
- Time signature (`TimeSignature`)
- Per-note metadata (velocity, duration)

The stream is then exported to both MIDI (`.mid`) and MusicXML (`.musicxml`) via music21's native exporters.

### 4.6 Stage 6: Audio Rendering (Optional)

`AudioRenderer` invokes FluidSynth with a configurable SoundFont file (`.sf2`) to synthesize the MIDI into PCM audio (WAV, 44100 Hz by default), with optional FFmpeg post-processing for MP3 encoding.

### 4.7 Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.9+ |
| LLM | OpenAI GPT-4o-mini (configurable) |
| Music Notation | music21 |
| Data Validation | Pydantic v2 |
| Audio Synthesis | FluidSynth + FFmpeg |
| Interface | argparse CLI + Python API |
| Testing | pytest with coverage |

---

## 5. Evaluation

### 5.1 Evaluation Methodology

Music generation quality is inherently subjective, so we employ both **automatic metrics** (objective, reproducible) and **qualitative analysis** (expert review of sample outputs).

#### 5.1.1 Automatic Metrics

| Metric | Definition |
|---|---|
| **Syllable-Note Alignment Accuracy** | Fraction of outputs where `len(notes) == total_syllables` |
| **Emotion-Key Consistency** | Fraction of outputs using a key consistent with the detected emotion per Table 1 |
| **Tempo Appropriateness** | Fraction of outputs with tempo within the expected BPM range for detected emotion |
| **MIDI Validity** | Fraction of MIDI files successfully parsed by music21 without errors |
| **LLM Success Rate** | Fraction of pipeline runs that completed without activating fallback |

#### 5.1.2 Qualitative Assessment

Three dimensions evaluated via expert listening:
1. **Melodic Coherence**: Smoothness of pitch progression, singability, phrase closure
2. **Emotional Alignment**: Perceived match between lyrical sentiment and musical mood
3. **Rhythmic Naturalness**: Naturalness of note duration patterns relative to speech rhythm

### 5.2 Test Dataset

We evaluated on 20 lyrical inputs designed to span the emotion space and lyric complexity:

| Dimension | Distribution |
|---|---|
| Emotion | Happy (5), Sad (5), Hopeful (4), Tense (3), Calm (2), Excited (1) |
| Length | Short (1 line, 5 samples), Medium (2–3 lines, 10 samples), Long (4+ lines, 5 samples) |
| Style | Literal/simple (10), Poetic/metaphorical (10) |

**Sample Test Cases:**

| ID | Lyrics | Emotion | Syllables |
|---|---|---|---|
| T1 | "The sun will rise again" | Hopeful | 6 |
| T2 | "Dancing in the moonlight, feeling so alive" | Happy | 12 |
| T3 | "Memories fade like photographs left in the rain" | Sad | 13 |
| T4 | "Shadows creeping closer, darkness all around" | Tense | 11 |
| T5 | "Gentle waves upon the shore, peaceful and serene" | Calm | 12 |

### 5.3 Quantitative Results

#### 5.3.1 Automatic Metrics

| Metric | Score | Details |
|---|---|---|
| Syllable-Note Alignment | **100%** | All 20/20 outputs matched syllable count exactly |
| Emotion-Key Consistency | **95%** | 19/20 used appropriate keys; 1 edge case with ambiguous mixed emotion |
| Tempo Appropriateness | **90%** | 18/20 within expected BPM ranges; 2 borderline outliers |
| MIDI Validity | **100%** | All 20/20 MIDI files parsed successfully by music21 |
| LLM Success Rate | **85%** | 17/20 runs used LLM-generated output; 3/20 activated fallback |

#### 5.3.2 Fallback Performance

Of the 3 cases that activated fallback:
- 2 were due to network timeout on LLM API calls
- 1 was due to a malformed JSON response (notes count mismatch)

All 3 fallback-generated melodies passed MIDI validity checks. Qualitative review rated fallback outputs as "mechanically correct but less expressive" compared to LLM outputs — a known tradeoff of deterministic generation.

#### 5.3.3 Latency Profile

| Operation | Mean Time |
|---|---|
| Emotion analysis (LLM) | ~1.4 s |
| Melody generation (LLM) | ~1.1 s |
| MIDI/MusicXML export | ~0.3 s |
| Audio rendering (WAV) | ~0.4 s |
| **End-to-end (with audio)** | **~3.2 s** |

### 5.4 Qualitative Analysis of Sample Outputs

**T1 — "The sun will rise again" (Hopeful, 6 syllables)**

- **Detected Emotion**: Hopeful | **Key**: G major | **Tempo**: 90 BPM | **Time Sig**: 4/4
- **Generated Melody**: G4 (0.5) → A4 (0.5) → B4 (1.0) → C5 (1.0) → B4 (0.5) → A4 (1.5)
- **Contour**: Ascending arch — rises to the phrase peak (C5) then resolves back
- **Assessment**: Musically coherent, emotionally appropriate ascending contour, all notes diatonic to G major, singable interval range (all within a 5th)

**T3 — "Memories fade like photographs left in the rain" (Sad, 13 syllables)**

- **Detected Emotion**: Sad | **Key**: A minor | **Tempo**: 65 BPM | **Time Sig**: 4/4
- **Generated Melody**: A4 → G4 → F4 → E4 → D4 → ... (stepwise descent)
- **Contour**: Descending with minor intervals; resolution on D4
- **Assessment**: Melancholic mood captured effectively via stepwise descent and slow tempo; avoids any major interval leaps inconsistent with the emotional register

### 5.5 Comparison with Related Systems

| System | Training Required | Output Format | Fallback | Open Source |
|---|---|---|---|---|
| Bao et al. (2018) [2] | Yes (large corpus) | MIDI | No | No |
| ReLyMe (2022) [3] | Yes | MIDI | Partial | No |
| SongComposer (2025) [5] | Yes (paired data) | MIDI + Lyrics | No | No |
| **L2M (Ours)** | **No** | **MIDI, MusicXML, WAV, MP3** | **Yes (deterministic)** | **Yes** |

**Advantages of L2M over supervised systems:**
- Zero training data or GPU resources required for deployment
- 100% completion rate via hybrid architecture
- Multiple output formats including playable audio
- Sub-5-second end-to-end latency

**Current limitations relative to fine-tuned systems:**
- Less sophisticated melodic structures (single-voice, no harmony)
- Limited style diversity without retraining
- Musical creativity bounded by LLM's zero-shot capability

---

## 6. Discussion

### 6.1 Key Findings

**Finding 1 — LLM Viability for Cross-Modal Generation:** GPT-4o-mini demonstrates sufficient musical knowledge to generate syllabically aligned, emotionally consistent melodies in a zero-shot setting. This suggests that LLM pre-training encodes substantial implicit music theory knowledge that can be elicited via structured prompting.

**Finding 2 — Prompt Engineering as a Core Technical Contribution:** The syllable-count hard constraint ("EXACTLY N notes") was critical — without explicit enforcement, early prompt versions produced note counts deviating by ±30% from the syllable count. Structured JSON schemas and few-shot examples reduced malformed response rates from ~35% (unstructured prompts) to ~15%.

**Finding 3 — Hybrid Architecture Value:** The deterministic fallback (3/20 activations, 15% rate) demonstrates that LLM-only pipelines are insufficient for production systems where reliability is required. The hybrid approach achieves 100% completion with graceful degradation rather than failure.

**Finding 4 — Two-Stage Decomposition:** Separating emotion analysis from melody generation provides two benefits: (a) interpretability — users can inspect and override the emotion reading before melody generation; (b) targeted fallback — if only melody generation fails, the correct emotional context is preserved for the fallback generator.

### 6.2 Limitations

1. **Harmonic Depth**: Generated melodies are monophonic. Chord progressions, harmonization, and countermelody are outside the current scope.
2. **Cultural Scope**: The emotion-key mapping and melodic contour algorithms reflect Western tonal music theory. Non-Western scales, modes, and rhythmic systems are not supported.
3. **Long-Form Coherence**: The chunking strategy for long lyrics maintains local melodic continuity (three-note context carryover) but does not enforce global structural coherence (e.g., return to the tonic at phrase boundaries).
4. **Evaluation Scale**: The 20-sample benchmark enables proof-of-concept validation but is insufficient for statistically robust claims about generalization.
5. **LLM API Dependency**: The primary generation path requires OpenAI API access, incurring per-request costs and introducing network latency.

### 6.3 Ethical Considerations

- **Copyright**: Generated melodies may inadvertently resemble copyrighted works. Users should exercise discretion before commercial use.
- **Attribution**: AI-generated content should be clearly disclosed, particularly in creative or academic contexts.
- **Access Equity**: API costs may create barriers to access for users in resource-constrained settings; local LLM support would address this.

---

## 7. Conclusion and Future Work

### 7.1 Conclusion

We presented **L2M**, an LLM-driven lyrics-to-melody system that achieves syllabic alignment, emotional coherence, and operational reliability without any task-specific training. The core technical insight is a two-stage prompting strategy — emotion analysis followed by conditioned melody generation — grounded in an explicit emotion-to-musical-attribute mapping, with a deterministic fallback layer ensuring 100% pipeline completion.

Quantitative evaluation demonstrates 100% syllable-note alignment, 95% emotion-key consistency, and 100% MIDI validity across a 20-sample benchmark. The system is released as an open-source Python package, providing an accessible, reproducible baseline for LLM-based music generation research.

The results suggest that zero-shot LLM prompting, when carefully engineered with structured constraints and few-shot examples, is a viable and practical alternative to supervised training for constrained creative generation tasks — particularly where training data is scarce and reliability is a requirement.

### 7.2 Future Work

#### 7.2.1 Harmonic Generation
- Extend to chord progression generation conditioned on the melodic output
- Support multi-voice arrangements (harmony, bass line, countermelody)
- Automatic instrumentation and orchestration

#### 7.2.2 Improved LLM Integration
- Evaluate larger models (GPT-4o, Claude 3.5 Sonnet) and open-source alternatives (LLaMA 3, Mistral) for both quality and cost-reliability tradeoffs
- Fine-tune a compact LLM on paired lyrics-melody data to improve creative quality while retaining the structural prompt framework
- Apply Reinforcement Learning from Human Feedback (RLHF) using musicologist-rated outputs

#### 7.2.3 Formal Evaluation
- Large-scale user study (musicians + general listeners, N ≥ 100) using Mean Opinion Score (MOS) and A/B comparison against ReLyMe and SongComposer
- Musicological analysis metrics: pitch class distribution entropy, interval histogram similarity to professional compositions, phrase boundary detection accuracy

#### 7.2.4 Non-Western Music Support
- Extend the emotion-key mapping to include maqam (Arabic), raga (Indian), and pentatonic (East Asian) systems
- Multi-language syllabification for non-English lyrics

#### 7.2.5 Interactive Generation
- Web-based GUI with real-time playback and in-browser melody editing
- Iterative refinement loop: user adjusts emotion label or key, system regenerates

---

## References

[1] Briot, J.-P., Hadjeres, G., & Pachet, F. (2020). Deep Learning Techniques for Music Generation. *Springer*.

[2] Bao, H., et al. (2018). Neural Melody Composition from Lyrics. *Proceedings of the 26th ACM International Conference on Multimedia (MM '18)*.

[3] Zhang, Y., et al. (2022). ReLyMe: Improving Lyric-to-Melody Generation by Incorporating Lyric-Melody Relationships. *arXiv preprint arXiv:2207.05688*.

[4] Zhang, Y., et al. (2023). Controllable Lyrics-to-Melody Generation. *arXiv preprint arXiv:2306.02613*.

[5] Ding, S., et al. (2024). SongComposer: A Large Language Model for Lyric and Melody Generation in Song Composition. *arXiv preprint arXiv:2402.17645*.

[6] Reddy, S., et al. (2023). Deep Attention-Based Alignment Network for Melody Generation from Incomplete Lyrics. *arXiv preprint arXiv:2301.10015*.

[7] Wang, L., et al. (2025). Melody-Lyrics Matching with Contrastive Alignment Loss. *arXiv preprint arXiv:2508.00123*.

[8] Li, Z., et al. (2025). AI-Enabled Text-to-Music Generation: A Comprehensive Review of Methods, Frameworks, and Future Directions. *MDPI Electronics*, 14(6), 1197.

[9] Mediakov, D., et al. (2024). Information Technology for Generating Lyrics for Song Extensions Based on Transformers. *International Journal of Modern Education and Computer Science*, 16(1).

[10] Gill, H., et al. (2020). Deep Learning in Musical Lyric Generation. *Yale Undergraduate Research Journal*, 1(1).

[11] OpenAI (2024). GPT-4 Technical Report. *OpenAI Research*.

[12] Cuthbert, M. S., & Ariza, C. (2010). music21: A Toolkit for Computer-Aided Musicology and Symbolic Music Data. *Proceedings of the International Society for Music Information Retrieval Conference (ISMIR)*.

[13] Brown, T., et al. (2020). Language Models Are Few-Shot Learners. *Advances in Neural Information Processing Systems (NeurIPS)*, 33.

---

## Appendix A: Installation and Configuration

### A.1 Prerequisites
- Python 3.9+
- OpenAI API key
- FluidSynth (optional, for audio rendering)
- FFmpeg (optional, for MP3 encoding)

### A.2 Quickstart

```bash
git clone <repository-url>
cd L2M
python -m venv venv && source venv/bin/activate
pip install -e .
cp .env.example .env
# Add OPENAI_API_KEY to .env
l2m --lyrics "The sun will rise again"
```

### A.3 Configuration Reference

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key | *(required)* |
| `MODEL_NAME` | GPT model identifier | `gpt-4o-mini` |
| `TEMPERATURE` | LLM sampling temperature | `0.7` |
| `MAX_TOKENS` | Maximum tokens per LLM call | `1500` |
| `SOUNDFONT_PATH` | Path to `.sf2` SoundFont file | `l2m/assets/soundfonts/...` |
| `AUDIO_SAMPLE_RATE` | Audio sample rate (Hz) | `44100` |
| `AUDIO_FORMAT` | Output audio format | `wav` |

---

## Appendix B: Extended Example Outputs

### B.1 Hopeful Lyrics

**Input:** `"The sun will rise again"`

**Emotion Analysis:**
```json
{
  "emotion": "hopeful",
  "tempo": 90,
  "time_signature": "4/4",
  "phrases": [{"line": "The sun will rise again", "syllables": 6}]
}
```

**Melody Structure:**
```json
{
  "key": "G major",
  "melody": [
    {"note": "G4", "duration": 0.5, "velocity": 64},
    {"note": "A4", "duration": 0.5, "velocity": 64},
    {"note": "B4", "duration": 1.0, "velocity": 70},
    {"note": "C5", "duration": 1.0, "velocity": 75},
    {"note": "B4", "duration": 0.5, "velocity": 70},
    {"note": "A4", "duration": 1.5, "velocity": 64}
  ]
}
```

### B.2 Sad Lyrics

**Input:** `"Memories fade like photographs left in the rain"`

**Emotion Analysis:**
```json
{
  "emotion": "sad",
  "tempo": 65,
  "time_signature": "4/4",
  "phrases": [{"line": "Memories fade like photographs left in the rain", "syllables": 13}]
}
```

**Melody Structure (partial):**
```json
{
  "key": "A minor",
  "melody": [
    {"note": "A4", "duration": 1.0},
    {"note": "G4", "duration": 1.0},
    {"note": "F4", "duration": 0.5},
    {"note": "E4", "duration": 0.5},
    {"note": "D4", "duration": 1.0}
    // ... 13 notes total
  ]
}
```

---

## Appendix C: Programmatic API Reference

```python
from l2m.llm.client import LLMClient
from l2m.services.lyric_parser import LyricParser
from l2m.services.melody_generator import MelodyGenerator
from l2m.services.midi_writer import MIDIWriter

# Initialize pipeline components
parser = LyricParser()
llm_client = LLMClient()
generator = MelodyGenerator(llm_client)
writer = MIDIWriter()

# Run pipeline
lyrics = "The sun will rise again"
normalized = parser.normalize(lyrics)
emotion_response = llm_client.analyze_emotion(normalized)
melody = generator.generate(normalized, emotion_response.analysis)
midi_path, xml_path = writer.write_both(melody, "output")
print(f"Generated MIDI: {midi_path}")
print(f"Generated MusicXML: {xml_path}")
```

---

## Acknowledgments

This work was supported by guidance from Dr. Mohammad Motiur Rahman. We acknowledge OpenAI for API access, the music21 development team for music notation infrastructure, and the Pydantic and FluidSynth communities for foundational tools used in this implementation.
