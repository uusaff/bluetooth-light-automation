"""
╔══════════════════════════════════════════════════════════════════╗
║          MOHUAN LED - PROFESSIONAL LIGHTING ENGINE               ║
║          Version 3.0 | 30+ Auto Effects | RGB Control            ║
╚══════════════════════════════════════════════════════════════════╝

Features:
  - 30+ automatic lighting effects across 6 categories
  - Non-blocking asyncio animation loop
  - Smooth transitions with configurable speed
  - Clean modular architecture (add new effects easily)
  - Bug-fixed input: invalid input never resets mode
"""

import asyncio
import sys
import math
import random
import colorsys
from bluelights import BJLEDInstance

# ──────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────
MAC_ADDRESS = "BE:30:17:00:00:A8"
UUID        = "0000ee02-0000-1000-8000-00805f9b34fb"

# Global control flags
_current_effect_task: asyncio.Task | None = None
_stop_event   = asyncio.Event()   # signals the running effect to stop


# ──────────────────────────────────────────────────────────────────
# HELPER UTILITIES
# ──────────────────────────────────────────────────────────────────

def hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    """Convert HSV (0‑1 each) → RGB (0‑255 each)."""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


async def set_rgb(led: BJLEDInstance, r: int, g: int, b: int):
    """Safely set LED color, clamp values 0‑255."""
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    await led.set_color_to_rgb(r, g, b)


async def sleep_or_stop(seconds: float) -> bool:
    """Sleep for `seconds`, but return True immediately if stop is signalled."""
    try:
        await asyncio.wait_for(_stop_event.wait(), timeout=seconds)
        return True   # stopped early
    except asyncio.TimeoutError:
        return False  # normal sleep completed


async def stop_current_effect():
    """Cancel the running effect task gracefully."""
    global _current_effect_task
    if _current_effect_task and not _current_effect_task.done():
        _stop_event.set()
        try:
            await asyncio.wait_for(_current_effect_task, timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            _current_effect_task.cancel()
    _stop_event.clear()
    _current_effect_task = None


def launch_effect(coro, led: BJLEDInstance) -> asyncio.Task:
    """Stop any running effect, then launch a new one."""
    global _current_effect_task
    # Schedule stop + launch through the event loop
    async def _runner():
        await stop_current_effect()
        _current_effect_task = asyncio.create_task(coro(led))
    asyncio.create_task(_runner())


# ──────────────────────────────────────────────────────────────────
# ░░ EFFECT LIBRARY ░░
# Each effect is an async function(led) that loops until _stop_event
# ──────────────────────────────────────────────────────────────────


# ── 🚓 FLASH / ALERT EFFECTS ──────────────────────────────────────

async def effect_police(led: BJLEDInstance):
    """Police lights – red/blue alternating fast."""
    while not _stop_event.is_set():
        await set_rgb(led, 255, 0, 0)
        if await sleep_or_stop(0.08): break
        await set_rgb(led, 0, 0, 255)
        if await sleep_or_stop(0.08): break
        await set_rgb(led, 255, 0, 0)
        if await sleep_or_stop(0.08): break
        await set_rgb(led, 0, 0, 0)
        if await sleep_or_stop(0.06): break
        await set_rgb(led, 0, 0, 255)
        if await sleep_or_stop(0.08): break
        await set_rgb(led, 0, 0, 0)
        if await sleep_or_stop(0.10): break


async def effect_fire_alarm(led: BJLEDInstance):
    """Fire alarm strobe – rapid white flashes."""
    while not _stop_event.is_set():
        await set_rgb(led, 255, 255, 255)
        if await sleep_or_stop(0.05): break
        await set_rgb(led, 0, 0, 0)
        if await sleep_or_stop(0.05): break


async def effect_emergency_pulse(led: BJLEDInstance):
    """Emergency warning – strong red pulse with breathing curve."""
    step = 0
    while not _stop_event.is_set():
        # Sine-wave pulsing for smooth breathe
        brightness = int((math.sin(step * 0.15) + 1) / 2 * 255)
        await set_rgb(led, brightness, 0, 0)
        if await sleep_or_stop(0.02): break
        step += 1


async def effect_sos(led: BJLEDInstance):
    """SOS Morse code (··· ─── ···) in white."""
    DOT  = 0.15
    DASH = 0.45
    GAP  = 0.10
    WORD = 0.80

    async def dot():
        await set_rgb(led, 255, 255, 255)
        if await sleep_or_stop(DOT): return True
        await set_rgb(led, 0, 0, 0)
        if await sleep_or_stop(GAP): return True
        return False

    async def dash():
        await set_rgb(led, 255, 255, 255)
        if await sleep_or_stop(DASH): return True
        await set_rgb(led, 0, 0, 0)
        if await sleep_or_stop(GAP): return True
        return False

    while not _stop_event.is_set():
        for _ in range(3):   # S
            if await dot(): break
        if _stop_event.is_set(): break
        if await sleep_or_stop(GAP * 2): break
        for _ in range(3):   # O
            if await dash(): break
        if _stop_event.is_set(): break
        if await sleep_or_stop(GAP * 2): break
        for _ in range(3):   # S
            if await dot(): break
        if _stop_event.is_set(): break
        if await sleep_or_stop(WORD): break


# ── 🎉 PARTY / DISCO EFFECTS ─────────────────────────────────────

async def effect_disco_chaos(led: BJLEDInstance):
    """Disco chaos – random color bursts at party speed."""
    while not _stop_event.is_set():
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(random.uniform(0.04, 0.12)): break


async def effect_club_strobe(led: BJLEDInstance):
    """Club strobe – RGB fast colour flashing."""
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
              (255, 255, 0), (0, 255, 255), (255, 0, 255), (255, 255, 255)]
    i = 0
    while not _stop_event.is_set():
        await set_rgb(led, *colors[i % len(colors)])
        if await sleep_or_stop(0.07): break
        await set_rgb(led, 0, 0, 0)
        if await sleep_or_stop(0.03): break
        i += 1


async def effect_party_wave(led: BJLEDInstance):
    """Party wave – hue shifts in a fast wave pattern."""
    step = 0
    while not _stop_event.is_set():
        hue = (step * 0.01) % 1.0
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.04): break
        step += 1


async def effect_beat_pulse(led: BJLEDInstance):
    """Beat pulse – simulates kick+snare rhythm at 128 BPM."""
    # 128 BPM = 0.469s per beat; kick every beat, snare every 2 beats
    beat   = 0.469
    while not _stop_event.is_set():
        # Kick – bright white pop
        await set_rgb(led, 255, 180, 60)
        if await sleep_or_stop(0.05): break
        await set_rgb(led, 30, 0, 60)
        if await sleep_or_stop(beat * 0.45): break
        # Snare – cyan pop
        await set_rgb(led, 0, 255, 220)
        if await sleep_or_stop(0.05): break
        await set_rgb(led, 30, 0, 60)
        if await sleep_or_stop(beat * 0.45): break


# ── 🌈 SMOOTH TRANSITION EFFECTS ─────────────────────────────────

async def effect_rainbow_wave(led: BJLEDInstance):
    """Classic rainbow cycle – continuous smooth hue rotation."""
    step = 0
    while not _stop_event.is_set():
        hue = (step / 360) % 1.0
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.018): break
        step = (step + 1) % 360


async def effect_slow_fade(led: BJLEDInstance):
    """Slow colour fade – drifts lazily through the spectrum."""
    step = 0
    while not _stop_event.is_set():
        hue = (step / 600) % 1.0
        r, g, b = hsv_to_rgb(hue, 0.9, 1.0)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.04): break
        step += 1


async def effect_gradient_shift(led: BJLEDInstance):
    """Gradient shift – warm‑to‑cool colour journey."""
    palette = [
        (255, 0,   128),   # hot pink
        (255, 80,  0  ),   # orange
        (255, 220, 0  ),   # gold
        (0,   220, 80 ),   # mint
        (0,   120, 255),   # sky blue
        (100, 0,   255),   # violet
        (200, 0,   180),   # purple
    ]
    idx  = 0
    sub  = 0
    STEPS = 80
    while not _stop_event.is_set():
        c1 = palette[idx % len(palette)]
        c2 = palette[(idx + 1) % len(palette)]
        t  = sub / STEPS
        r  = int(c1[0] + (c2[0] - c1[0]) * t)
        g  = int(c1[1] + (c2[1] - c1[1]) * t)
        b  = int(c1[2] + (c2[2] - c1[2]) * t)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.035): break
        sub += 1
        if sub >= STEPS:
            sub = 0
            idx = (idx + 1) % len(palette)


async def effect_calm_breathing(led: BJLEDInstance):
    """Calm breathing RGB – slow inhale/exhale in soft purple."""
    step = 0
    while not _stop_event.is_set():
        t  = (math.sin(step * 0.05) + 1) / 2   # 0 → 1 → 0
        r  = int(120 * t)
        g  = int(40  * t)
        b  = int(200 * t)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.03): break
        step += 1


async def effect_sunset(led: BJLEDInstance):
    """Sunset mode – warm orange/red/violet slow drift."""
    keyframes = [
        (255, 200, 50 ),   # golden hour
        (255, 120, 20 ),   # deep orange
        (220, 40,  10 ),   # red horizon
        (140, 20,  80 ),   # dusk violet
        (60,  10,  100),   # twilight
        (20,  5,   60 ),   # night
        (60,  10,  100),   # back through twilight
        (140, 20,  80 ),
        (220, 40,  10 ),
        (255, 120, 20 ),
    ]
    idx  = 0
    sub  = 0
    STEPS = 120
    while not _stop_event.is_set():
        c1 = keyframes[idx % len(keyframes)]
        c2 = keyframes[(idx + 1) % len(keyframes)]
        t  = sub / STEPS
        r  = int(c1[0] + (c2[0] - c1[0]) * t)
        g  = int(c1[1] + (c2[1] - c1[1]) * t)
        b  = int(c1[2] + (c2[2] - c1[2]) * t)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.05): break
        sub += 1
        if sub >= STEPS:
            sub = 0
            idx = (idx + 1) % len(keyframes)


async def effect_ocean(led: BJLEDInstance):
    """Ocean – gentle blue/teal wave breathing."""
    step = 0
    while not _stop_event.is_set():
        t  = (math.sin(step * 0.04) + 1) / 2
        r  = int(0   + 20  * t)
        g  = int(80  + 120 * t)
        b  = int(150 + 105 * t)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.03): break
        step += 1


# ── ⚡ FAST DYNAMIC EFFECTS ───────────────────────────────────────

async def effect_lightning(led: BJLEDInstance):
    """Lightning strike – random bright flashes with dark gaps."""
    while not _stop_event.is_set():
        # Long dark pause before strike
        if await sleep_or_stop(random.uniform(0.3, 1.2)): break
        # 1-3 flash bursts
        flashes = random.randint(1, 3)
        for _ in range(flashes):
            brightness = random.randint(180, 255)
            await set_rgb(led, brightness, brightness, int(brightness * 0.8))
            if await sleep_or_stop(random.uniform(0.02, 0.07)): break
            await set_rgb(led, 0, 0, 0)
            if await sleep_or_stop(random.uniform(0.02, 0.05)): break
        if _stop_event.is_set(): break


async def effect_spark_burst(led: BJLEDInstance):
    """Spark burst – random bright colour pop then fade to dark."""
    while not _stop_event.is_set():
        hue = random.random()
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.04): break
        # Quick dim-down
        for step in range(8, 0, -1):
            factor = step / 8
            await set_rgb(led, int(r*factor), int(g*factor), int(b*factor))
            if await sleep_or_stop(0.02): break
        await set_rgb(led, 0, 0, 0)
        if await sleep_or_stop(random.uniform(0.05, 0.20)): break


async def effect_fire_flicker(led: BJLEDInstance):
    """Fire flicker – organic red/orange/yellow flame simulation."""
    while not _stop_event.is_set():
        r = random.randint(200, 255)
        g = random.randint(30, 100)
        b = random.randint(0, 10)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(random.uniform(0.03, 0.10)): break


async def effect_glitch(led: BJLEDInstance):
    """Glitch mode – corrupted signal random flickers."""
    glitch_colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (0, 255, 255), (255, 0, 255),
        (255, 255, 255), (0, 0, 0),
    ]
    while not _stop_event.is_set():
        if random.random() < 0.3:
            # Rapid glitch burst
            for _ in range(random.randint(2, 6)):
                await set_rgb(led, *random.choice(glitch_colors))
                if await sleep_or_stop(random.uniform(0.02, 0.06)): break
        else:
            # Hold a colour briefly
            await set_rgb(led, *random.choice(glitch_colors))
            if await sleep_or_stop(random.uniform(0.08, 0.25)): break


async def effect_meteor(led: BJLEDInstance):
    """Meteor – bright cyan streak fades to deep space blue."""
    step = 0
    while not _stop_event.is_set():
        t = (step % 100) / 100
        if t < 0.1:
            # Bright head
            br = int(255 * (t / 0.1))
            await set_rgb(led, 0, br, int(br * 0.8))
        elif t < 0.5:
            # Fading trail
            br = int(255 * (1 - (t - 0.1) / 0.4))
            await set_rgb(led, 0, br // 4, br)
        else:
            # Dark space
            await set_rgb(led, 0, 0, 10)
        if await sleep_or_stop(0.02): break
        step += 1


# ── 🧠 PATTERN-BASED EFFECTS ──────────────────────────────────────

async def effect_knight_rider(led: BJLEDInstance):
    """Knight Rider / Larson scanner – red swoosh back and forth."""
    STEPS = 20
    step  = 0
    direction = 1
    while not _stop_event.is_set():
        brightness = int(abs(math.sin(step / STEPS * math.pi)) * 255)
        r = brightness
        g = brightness // 8
        b = 0
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.03): break
        step += direction
        if step >= STEPS or step <= 0:
            direction *= -1


async def effect_ping_pong(led: BJLEDInstance):
    """Ping-pong – colour bounces between warm and cool."""
    step = 0
    direction = 1
    MAX = 60
    while not _stop_event.is_set():
        t   = step / MAX
        r   = int(255 * t)
        g   = 0
        b   = int(255 * (1 - t))
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.025): break
        step += direction
        if step >= MAX or step <= 0:
            direction *= -1


async def effect_spiral(led: BJLEDInstance):
    """Spiral – hue rotates with oscillating brightness."""
    step = 0
    while not _stop_event.is_set():
        hue = (step * 0.008) % 1.0
        val = (math.sin(step * 0.12) + 1) / 2 * 0.7 + 0.3
        r, g, b = hsv_to_rgb(hue, 1.0, val)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.025): break
        step += 1


async def effect_expand_wave(led: BJLEDInstance):
    """Expanding/shrinking wave – pulses outward like a sonar ping."""
    step = 0
    while not _stop_event.is_set():
        # Sawtooth: 0→1 quickly, then reset
        t   = (step % 40) / 40
        hue = (step * 0.005) % 1.0
        val = 1 - t            # brightest at start, fades out
        r, g, b = hsv_to_rgb(hue, 1.0, val)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.025): break
        step += 1


async def effect_mirror_bounce(led: BJLEDInstance):
    """Symmetric mirror bounce – dual-tone symmetric oscillation."""
    step = 0
    while not _stop_event.is_set():
        t   = (math.sin(step * 0.07) + 1) / 2
        r   = int(255 * t)
        g   = int(255 * (1 - t))
        b   = int(128 + 127 * math.sin(step * 0.05))
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.025): break
        step += 1


# ── 🎮 CREATIVE / FUN EFFECTS ─────────────────────────────────────

async def effect_matrix_rain(led: BJLEDInstance):
    """Matrix rain – cascading bright green flickers on deep green."""
    step = 0
    while not _stop_event.is_set():
        if random.random() < 0.4:
            g = random.randint(180, 255)
            r = random.randint(0, 20)
            b = random.randint(0, 10)
        else:
            g = random.randint(20, 80)
            r = 0
            b = 0
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.04): break
        step += 1


async def effect_color_chase(led: BJLEDInstance):
    """Color chase – rapid spectrum chase with brief trails."""
    colors = [hsv_to_rgb(i / 12, 1.0, 1.0) for i in range(12)]
    i = 0
    while not _stop_event.is_set():
        await set_rgb(led, *colors[i % len(colors)])
        if await sleep_or_stop(0.08): break
        # Dim trail
        r, g, b = colors[i % len(colors)]
        await set_rgb(led, r // 3, g // 3, b // 3)
        if await sleep_or_stop(0.04): break
        i += 1


async def effect_pixel_explosion(led: BJLEDInstance):
    """Random pixel explosion – chaotic bright burst every cycle."""
    while not _stop_event.is_set():
        # Burst phase: rapid random colours
        for _ in range(random.randint(5, 15)):
            await set_rgb(led,
                          random.randint(100, 255),
                          random.randint(0,   255),
                          random.randint(0,   255))
            if await sleep_or_stop(0.03): break
        if _stop_event.is_set(): break
        # Fade out to black
        for v in range(10, -1, -1):
            factor = v / 10
            await set_rgb(led, int(200 * factor), int(100 * factor), int(200 * factor))
            if await sleep_or_stop(0.02): break
        if await sleep_or_stop(0.1): break


async def effect_wave_interference(led: BJLEDInstance):
    """Wave interference – two sine waves interfering to create moiré."""
    step = 0
    while not _stop_event.is_set():
        wave1 = (math.sin(step * 0.07) + 1) / 2
        wave2 = (math.sin(step * 0.13 + 1.5) + 1) / 2
        mixed = (wave1 + wave2) / 2
        r = int(255 * wave1)
        g = int(255 * mixed)
        b = int(255 * wave2)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.025): break
        step += 1


async def effect_neon_cyber(led: BJLEDInstance):
    """Neon cyber pulse – electric cyan/magenta rapid neon strobe."""
    neon = [
        (0, 255, 255),    # cyan
        (255, 0, 255),    # magenta
        (0, 255, 180),    # electric green
        (180, 0, 255),    # violet
        (255, 50, 200),   # hot pink
    ]
    step = 0
    while not _stop_event.is_set():
        idx  = (step // 3) % len(neon)
        phase = step % 3
        if phase == 0:
            await set_rgb(led, *neon[idx])
        elif phase == 1:
            r, g, b = neon[idx]
            await set_rgb(led, r // 2, g // 2, b // 2)
        else:
            await set_rgb(led, 0, 0, 0)
        if await sleep_or_stop(0.07): break
        step += 1


async def effect_aurora(led: BJLEDInstance):
    """Aurora borealis – dreamy green/blue/violet shimmer."""
    step = 0
    while not _stop_event.is_set():
        hue = 0.30 + 0.20 * math.sin(step * 0.03)   # green → teal → blue
        sat = 0.7  + 0.3  * math.sin(step * 0.07)
        val = 0.5  + 0.5  * math.sin(step * 0.05)
        r, g, b = hsv_to_rgb(hue % 1.0, sat, val)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.04): break
        step += 1


async def effect_lava_lamp(led: BJLEDInstance):
    """Lava lamp – slow warm blobs drifting orange/red/yellow."""
    step = 0
    while not _stop_event.is_set():
        r = int(200 + 55  * math.sin(step * 0.04))
        g = int(50  + 80  * math.sin(step * 0.06 + 1))
        b = int(5   + 15  * math.sin(step * 0.03 + 2))
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.04): break
        step += 1


async def effect_candy(led: BJLEDInstance):
    """Candy – sweet pastel cycling through pink, mint, lavender."""
    pastels = [
        (255, 150, 180),  # candy pink
        (150, 255, 200),  # mint
        (200, 150, 255),  # lavender
        (255, 220, 150),  # peach
        (150, 220, 255),  # baby blue
    ]
    idx  = 0
    sub  = 0
    STEPS = 60
    while not _stop_event.is_set():
        c1 = pastels[idx % len(pastels)]
        c2 = pastels[(idx + 1) % len(pastels)]
        t  = sub / STEPS
        r  = int(c1[0] + (c2[0] - c1[0]) * t)
        g  = int(c1[1] + (c2[1] - c1[1]) * t)
        b  = int(c1[2] + (c2[2] - c1[2]) * t)
        await set_rgb(led, r, g, b)
        if await sleep_or_stop(0.04): break
        sub += 1
        if sub >= STEPS:
            sub = 0
            idx = (idx + 1) % len(pastels)


async def effect_heartbeat(led: BJLEDInstance):
    """Heartbeat – double thump (lub-dub) in deep red."""
    while not _stop_event.is_set():
        # Lub
        await set_rgb(led, 255, 0, 20)
        if await sleep_or_stop(0.08): break
        await set_rgb(led, 60, 0, 5)
        if await sleep_or_stop(0.10): break
        # Dub (slightly softer)
        await set_rgb(led, 200, 0, 15)
        if await sleep_or_stop(0.07): break
        await set_rgb(led, 60, 0, 5)
        if await sleep_or_stop(0.10): break
        # Rest
        await set_rgb(led, 0, 0, 0)
        if await sleep_or_stop(0.55): break


async def effect_deep_space(led: BJLEDInstance):
    """Deep space – dark ambient with random star twinkles."""
    while not _stop_event.is_set():
        if random.random() < 0.15:
            # Twinkle
            b = random.randint(150, 255)
            await set_rgb(led, b, b, b)
            if await sleep_or_stop(0.05): break
        await set_rgb(led, 0, 0, random.randint(5, 20))
        if await sleep_or_stop(random.uniform(0.08, 0.25)): break


# ──────────────────────────────────────────────────────────────────
# EFFECT REGISTRY
# ──────────────────────────────────────────────────────────────────

EFFECTS = {
    # ── 🚓 Flash / Alert ───────────────────────
    "10": ("🚓 Police Lights",         effect_police),
    "11": ("🔥 Fire Alarm Strobe",     effect_fire_alarm),
    "12": ("🔴 Emergency Pulse",       effect_emergency_pulse),
    "13": ("🆘 SOS Morse Code",        effect_sos),

    # ── 🎉 Party / Disco ───────────────────────
    "20": ("🎲 Disco Chaos",           effect_disco_chaos),
    "21": ("🕺 Club Strobe",           effect_club_strobe),
    "22": ("🌊 Party Wave",            effect_party_wave),
    "23": ("🥁 Beat Pulse (128 BPM)", effect_beat_pulse),

    # ── 🌈 Smooth Transitions ─────────────────
    "30": ("🌈 Rainbow Wave",          effect_rainbow_wave),
    "31": ("🎨 Slow Colour Fade",      effect_slow_fade),
    "32": ("🔀 Gradient Shift",        effect_gradient_shift),
    "33": ("😮‍💨 Calm Breathing",      effect_calm_breathing),
    "34": ("🌅 Sunset Mode",           effect_sunset),
    "35": ("🌊 Ocean Drift",           effect_ocean),

    # ── ⚡ Fast Dynamic ────────────────────────
    "40": ("⚡ Lightning Strike",      effect_lightning),
    "41": ("✨ Spark Burst",           effect_spark_burst),
    "42": ("🔥 Fire Flicker",          effect_fire_flicker),
    "43": ("📺 Glitch Mode",           effect_glitch),
    "44": ("☄️ Meteor Trail",          effect_meteor),

    # ── 🧠 Pattern-Based ──────────────────────
    "50": ("🚗 Knight Rider",          effect_knight_rider),
    "51": ("🏓 Ping-Pong",             effect_ping_pong),
    "52": ("🌀 Spiral Rotate",         effect_spiral),
    "53": ("📡 Expand Wave",           effect_expand_wave),
    "54": ("🔀 Mirror Bounce",         effect_mirror_bounce),

    # ── 🎮 Creative / Fun ─────────────────────
    "60": ("💻 Matrix Rain",           effect_matrix_rain),
    "61": ("🏎️ Colour Chase",          effect_color_chase),
    "62": ("💥 Pixel Explosion",       effect_pixel_explosion),
    "63": ("〰️ Wave Interference",     effect_wave_interference),
    "64": ("🌐 Neon Cyber Pulse",      effect_neon_cyber),
    "65": ("🌌 Aurora Borealis",       effect_aurora),
    "66": ("🫧 Lava Lamp",             effect_lava_lamp),
    "67": ("🍭 Candy Pastel",          effect_candy),
    "68": ("❤️ Heartbeat",            effect_heartbeat),
    "69": ("🌠 Deep Space",            effect_deep_space),
}

# ──────────────────────────────────────────────────────────────────
# MENU DISPLAY
# ──────────────────────────────────────────────────────────────────

def print_main_menu():
    print("\n" + "═" * 52)
    print("  ✨  MOHUAN LED — PROFESSIONAL LIGHTING ENGINE  ✨")
    print("═" * 52)
    print("  1  💡 Turn ON         2  🔌 Turn OFF")
    print("  3  🎨 Quick Colors    4  🖌️  Custom RGB")
    print("  5  🎬 Auto Effects    6  ⏹️  Stop Effect")
    print("  7  🚪 Exit")
    print("═" * 52)


def print_effects_menu():
    categories = {
        "🚓 FLASH / ALERT": [k for k in EFFECTS if k.startswith("1")],
        "🎉 PARTY / DISCO" : [k for k in EFFECTS if k.startswith("2")],
        "🌈 SMOOTH TRANS." : [k for k in EFFECTS if k.startswith("3")],
        "⚡ FAST DYNAMIC"  : [k for k in EFFECTS if k.startswith("4")],
        "🧠 PATTERN-BASED" : [k for k in EFFECTS if k.startswith("5")],
        "🎮 CREATIVE / FUN": [k for k in EFFECTS if k.startswith("6")],
    }
    print("\n" + "═" * 52)
    print("  🎬  AUTOMATIC LIGHTING EFFECTS  🎬")
    print("═" * 52)
    for cat, keys in categories.items():
        print(f"\n  {cat}")
        for k in keys:
            name, _ = EFFECTS[k]
            print(f"    [{k}] {name}")
    print("\n  [0]  ← Back to Main Menu")
    print("═" * 52)


# ──────────────────────────────────────────────────────────────────
# INPUT HELPER  (non-blocking using asyncio executor)
# ──────────────────────────────────────────────────────────────────

async def ainput(prompt: str = "") -> str:
    """Async wrapper around blocking input()."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: input(prompt))


# ──────────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ──────────────────────────────────────────────────────────────────

async def run_app():
    global _current_effect_task

    print("\n🚀 Connecting to MohuanLED …")
    led = BJLEDInstance(address=MAC_ADDRESS, uuid=UUID)

    try:
        await led.turn_on()
        print("✅ Connected! Lights are ON.\n")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # ── Main Loop ────────────────────────────────────────────────
    while True:
        print_main_menu()
        choice = (await ainput("👉 Enter option (1-7): ")).strip()

        # ── 1: Turn ON ───────────────────────────────────────────
        if choice == "1":
            await stop_current_effect()
            print("💡 Turning ON …")
            await led.turn_on()

        # ── 2: Turn OFF ──────────────────────────────────────────
        elif choice == "2":
            await stop_current_effect()
            print("🔌 Turning OFF …")
            await led.turn_off()

        # ── 3: Quick Colors ───────────────────────────────────────
        elif choice == "3":
            await stop_current_effect()
            sub = (await ainput(
                "  Type R=Red  G=Green  B=Blue  W=White  Y=Yellow  C=Cyan  P=Purple: "
            )).strip().upper()
            color_map = {
                "R": (255, 0,   0  ), "G": (0,   255, 0  ),
                "B": (0,   0,   255), "W": (255, 255, 255),
                "Y": (255, 220, 0  ), "C": (0,   255, 220),
                "P": (180, 0,   255),
            }
            if sub in color_map:
                await set_rgb(led, *color_map[sub])
                print(f"  ✅ Colour set!")
            else:
                print("  ⚠️  Invalid input, please try again.")

        # ── 4: Custom RGB ─────────────────────────────────────────
        elif choice == "4":
            await stop_current_effect()
            try:
                r = int((await ainput("  Red   (0-255): ")).strip())
                g = int((await ainput("  Green (0-255): ")).strip())
                b = int((await ainput("  Blue  (0-255): ")).strip())
                await set_rgb(led, r, g, b)
                print(f"  🎨 RGB({r}, {g}, {b}) applied!")
            except ValueError:
                print("  ⚠️  Invalid input — please enter numbers 0-255.")

        # ── 5: Auto Effects ───────────────────────────────────────
        elif choice == "5":
            while True:
                print_effects_menu()
                eff = (await ainput("👉 Enter effect code (or 0 to go back): ")).strip()

                if eff == "0":
                    break
                elif eff in EFFECTS:
                    name, coro_fn = EFFECTS[eff]
                    print(f"\n  ▶️  Starting: {name}")
                    await stop_current_effect()
                    _current_effect_task = asyncio.create_task(coro_fn(led))
                    print("  ✅ Effect running. Press 6 from main menu to stop.")
                    break   # Return to main menu; effect runs in background
                else:
                    print("  ⚠️  Invalid input, please try again.")

        # ── 6: Stop Effect ────────────────────────────────────────
        elif choice == "6":
            if _current_effect_task and not _current_effect_task.done():
                print("  ⏹️  Stopping current effect …")
                await stop_current_effect()
                await set_rgb(led, 60, 0, 120)   # Return to dim purple idle
                print("  ✅ Effect stopped. Lights set to idle colour.")
            else:
                print("  ℹ️  No effect is currently running.")

        # ── 7: Exit ───────────────────────────────────────────────
        elif choice == "7":
            print("\n  🔌 Stopping effects and turning off …")
            await stop_current_effect()
            await led.turn_off()
            try:
                await led._disconnect()
            except Exception:
                pass
            print("  👋 Allah Hafiz! Goodbye.\n")
            break

        # ── Invalid Input ─────────────────────────────────────────
        else:
            print("  ⚠️  Invalid input, please try again.")
            # Current mode/effect keeps running — nothing is reset


# ──────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_app())