import platform
import random

from .iterutils import iterate

try:  # pragma: no cover
    import winsound

    def _do_play(track):
        for freq, ms in track:
            winsound.Beep(freq, ms)
except ImportError:  # pragma: no cover
    from . import shell

    def _do_play(track):
        try:
            shell.which('beep')
            args = []
            for freq, ms in track:
                args.extend(['-n', '-f', freq, '-l', ms])
            args[0] = 'beep'
        except IOError:
            args = ['play', '-q']
            note = '|sox -n -p synth {} sawtooth {}'
            for freq, ms in track:
                args.append(note.format(ms / 1000.0, freq))
                args.append(note.format(ms / 8000.0, 0))
            args.extend(['vol', '-20dB'])

        try:
            shell.execute(args, stdout=shell.Mode.devnull,
                          stderr=shell.Mode.devnull)
        except OSError:
            raise ValueError("'sound player not found; install 'beep' or " +
                             "'sox' package?")


def riff(a, b, hold=3.5):
    def gen():
        for i, v in enumerate(b):
            yield a, 1
            yield a, 1
            d = 1 if i < len(b) - 1 else hold
            for j in iterate(v):
                yield j, d

    return list(gen())


E3 = 165
F3 = 175
FS3 = 185
G3 = 196
A3 = 220
B3 = 247
CS4 = 277
DS4 = 311
E4 = 330
F4 = 349
G4 = 392
GS4 = 415
A4 = 440
B4 = 494
CS5 = 554

e1m1_1 = riff(E3, (B3, A3, G3, F3, (FS3, G3), B3, A3, G3, F3))
e1m1_2 = riff(A3, (A4, G4, F4, DS4, (E4, F4), A4, G4, F4, DS4))
e1m1_3 = (riff(CS4, (CS5, B4, A4, G4, (GS4, A4)), hold=1) +
          riff(B3, (B4, A4, G4), hold=1) + riff(A3, (F4,)))

e1m1 = e1m1_1 * 2 + e1m1_2 + e1m1_1 + e1m1_3 + e1m1_1

plat = platform.system()
msgs = [
    "Please don't leave, there's more demons to toast!",
    "Let's beat it -- This is turning into a bloodbath!",
    "I wouldn't leave if I were you. {} is much worse.".format(plat),
    "You're trying to say you like {} better than me, right?".format(plat),
    "Don't leave yet -- There's a demon around that corner!",
    "Ya know, next time you come in here I'm gonna toast ya.",
    'Go ahead and leave. See if I care.',
    'Are you sure you want to quit this great music?',
]


def play(tempo, long):
    try:
        _do_play((freq, int(dur * 15000 / tempo))
                 for freq, dur in (e1m1 if long else e1m1_1))
    except KeyboardInterrupt:  # pragma: no cover
        print(random.choice(msgs))
        exit(1)
