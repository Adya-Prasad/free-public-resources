"""
### Some information about this program and music

This AI program demonstrates how to algorithmically generate a short music by layering basic musical elements:
The 8 Elements of Music are, in alphabetical order, Dynamics, Form, Harmony, Melody, Rhythm, Texture, Timbre and Tonality

1. **Melody**: A sequence of pitches drawn from a C major scale, probabilistically aligned to a chord progression and enriched with a short motif.
2. **Arpeggio**: Broken chords (arpeggios) that play chord tones in ascending, descending, or random order to fill rhythmic space.
3. **Bassline**: A simple root‑note bass pattern that follows the chord progression in whole‑note durations.
4. **Drums**: Basic percussion with kick, snare, hi‑hat, and occasional snare fills to create a steady groove.

Key musical concepts:
- **Scale**: In C major (C, D, E, F, G, A, B), the foundation of all pitch choices.
- **Chord**: Combinations of three notes (triads) built on scale degrees (I, V, vi, IV, etc.).
- **Chord Progression**: A sequence of chords (e.g. I–V–vi–IV) that establishes harmonic movement.
- **Motif**: A small melodic idea (short sequence of notes) that recurs to give coherence.
- **Arpeggio**: Playing the notes of a chord in sequence rather than simultaneously.
- **Layering**: Combining multiple musical lines (melody, harmony, bass, rhythm) into one mix.
- **Normalization**: Scaling the final audio so its peaks sit at a safe amplitude, avoiding clipping.

Implementation details:
- **Sine waves** generate pure tones for melody, arpeggio, and bass.
- **Exponential decay** and noise simulate percussive timbres for drums.
- **Event lists** store (pitch_or_type, duration, start_time) tuples for each layer.
- **Buffer mixing** adds each event into a NumPy array of samples.
- **MP3 encoding** uses a pure‑Python LAME wrapper (`lameenc`) to output a `.mp3` file.

Dependencies: numpy and lamneec, if don't have, use the below command:
pip install numpy lameenc
"""

import numpy as np
import random, os, time
import lameenc

# Seed for variability
random.seed(time.time())

# Constants
SR       = 44100
DURATION = 15  # seconds

# Note frequencies
note_freqs = {
    "C3":130.81,"D3":146.83,"E3":164.81,"F3":174.61,"G3":196.00,
    "A3":220.00,"B3":246.94,"C4":261.63,"D4":293.66,"E4":329.63,
    "F4":349.23,"G4":392.00,"A4":440.00,"B4":493.88,"C5":523.25,
    "D5":587.33,"E5":659.25
}

# Chord tones (including E3 → E minor)
chord_notes = {
    "C3":["C4","E4","G4"],
    "G3":["G4","B4","D5"],
    "A3":["A4","C5","E5"],
    "F3":["F4","A4","C5"],
    "E3":["E3","G3","B3"],
}

# Possible progressions, expanded for variety
chord_progressions = [
    ["C3","G3","A3","F3"],  
    ["A3","F3","C3","G3"],  
    ["F3","G3","E3","A3"],  
    ["C3","A3","F3","G3"],  # love 
    ["C3","F3","G3","C3"],  # party
    ["A3","F3","G3","C3"],  # pop
]

scale = ["C4","D4","E4","F4","G4","A4","B4","C5"]

# Unique-filename helper
def get_unique_filename(base, ext):
    name = f"{base}{ext}"
    i = 1
    while os.path.exists(name):
        name = f"{base} ({i}){ext}"
        i += 1
    return name

# Waveform generators
def sine_wave(freq, dur, decay_factor=0):
    t = np.linspace(0, dur, int(SR*dur), False)
    wave = np.sin(2*np.pi*freq*t)
    if decay_factor > 0:
        envelope = np.exp(-t / dur * decay_factor)
        wave *= envelope
    return wave

def drum_sound(kind, dur):
    t = np.linspace(0, dur, int(SR*dur), False)
    if kind=="kick":
        return np.sin(2*np.pi*55*t)*np.exp(-t*30)
    if kind=="snare":
        return (0.8*np.sin(2*np.pi*180*t) + 0.2*np.random.rand(len(t))) * np.exp(-t*20)
    if kind=="hihat":
        return np.random.rand(len(t)) * np.exp(-t*60) * 0.4
    if kind=="clap":
        return np.random.rand(len(t)) * np.exp(-t*40) * 0.6
    return np.zeros(len(t))

# Mixer with clamping to buffer end
def add_events(buf, events, gen_fn, vol):
    N = buf.shape[0]
    for name, dur, start in events:
        i0 = int(start * SR)
        data = gen_fn(name, dur) * vol
        i1 = min(i0 + data.shape[0], N)
        if i0 < N:
            buf[i0:i1] += data[:i1-i0]

# Melody generator, updated for livelier rhythm
def make_melody(prog, bpm, motif):
    beat = 60/bpm
    chord_len = 4*beat
    t = 0
    out = []
    while t < DURATION:
        root = prog[int(t/chord_len) % len(prog)]
        pool = chord_notes[root] if random.random() < 0.7 else scale
        note = random.choice(pool)
        if random.random() < 0.2:
            note = random.choice(motif)
        dur = min(random.choices([0.5,1.0,2.0], weights=[0.4,0.4,0.2])[0] * beat,
                  DURATION - t)
        out.append((note, dur, t))
        t += dur
    return out

# Arpeggio generator
def make_arpeggio(prog, bpm):
    beat = 60/bpm
    step = 0.5*beat
    t = idx = 0
    style = random.choice(['asc','desc','rand'])
    out = []
    while t < DURATION:
        root = prog[int(t/(4*beat)) % len(prog)]
        notes = chord_notes[root][:]
        if style=='asc':   notes.sort(key=lambda n: note_freqs[n])
        if style=='desc':  notes.sort(key=lambda n: note_freqs[n], reverse=True)
        if style=='rand':  random.shuffle(notes)
        dur = min(step, DURATION - t)
        out.append((notes[idx % len(notes)], dur, t))
        t += dur; idx += 1
    return out

# Bassline generator
def make_bass(prog, bpm):
    beat = 60/bpm
    t = idx = 0
    out = []
    while t < DURATION:
        root = prog[idx % len(prog)]
        dur = min(4*beat, DURATION - t)
        out.append((root, dur, t))
        t += dur; idx += 1
    return out

# Pads generator for relaxing background
def make_pads(prog, bpm):
    beat = 60/bpm
    chord_dur = 4*beat
    t = idx = 0
    out = []
    while t < DURATION:
        root = prog[idx % len(prog)]
        notes = chord_notes[root]
        dur = min(chord_dur, DURATION - t)
        for note in notes:
            out.append((note, dur, t))
        t += chord_dur
        idx += 1
    return out

# Drums generator
def make_drums(bpm):
    beat = 60/bpm
    out = []
    for i in range(int(DURATION/beat)):
        start = i * beat
        b = (i % 4) + 1
        if b in (1,3): out.append(("kick", 0.08, start))
        if b in (2,4):
            out.append(("snare", 0.08, start))
            if start > DURATION/2:
                out.append(("clap", 0.08, start))
        out.append(("hihat", 0.06, start))
        out.append(("hihat", 0.04, start + 0.25*beat))
        if random.random() < 0.1:
            for j in range(4):
                out.append(("snare", 0.05, start + j*0.05))
    return out

# === Build & mix ===
bpm   = random.randint(110, 140)
prog  = random.choice(chord_progressions)
motif = [random.choice(scale) for _ in range(3)]

melody   = make_melody(prog, bpm, motif)
arpeggio = make_arpeggio(prog, bpm)
bassline = make_bass(prog, bpm)
pads     = make_pads(prog, bpm)
drums    = make_drums(bpm)

buffer = np.zeros(int(DURATION*SR), dtype=float)

add_events(buffer, melody,   lambda n,d: sine_wave(note_freqs[n], d, 3), 0.9)
add_events(buffer, arpeggio, lambda n,d: sine_wave(note_freqs[n], d, 3), 0.3)
add_events(buffer, bassline, lambda n,d: sine_wave(note_freqs[n], d, 0), 0.7)
add_events(buffer, pads,     lambda n,d: sine_wave(note_freqs[n], d, 0.5), 0.2)
add_events(buffer, drums,    lambda k,d: drum_sound(k, d), 1.0)

# Normalize to [-1,1]
buffer *= 0.9 / np.max(np.abs(buffer))

# Convert to 16-bit PCM bytes
pcm = (buffer * 32767).astype(np.int16).tobytes()

# Encode to MP3 with lameenc
encoder = lameenc.Encoder()
encoder.set_bit_rate(192)
encoder.set_in_sample_rate(SR)
encoder.set_channels(1)

mp3_data = encoder.encode(pcm)
mp3_data += encoder.flush()

# Write out file
fn_mp3 = get_unique_filename("simple_ai_generated_music", ".mp3")
with open(fn_mp3, "wb") as f:
    f.write(mp3_data)

print(f"Music generated and saved to: {fn_mp3}")
