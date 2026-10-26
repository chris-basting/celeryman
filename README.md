# Celery Man

*Computer, load up Celery Man please.*

A terminal toy based on the Tim & Eric "Celery Man" sketch. Type commands into
Paul's COMPUTER and watch retro windows full of dancing pixel-art characters
pile up on a Windows 3.1-style desktop.

This is an unofficial fan project, made for fun. It isn't affiliated with or
endorsed by Tim & Eric or anyone involved with the sketch. All the character
art is original.

## Requirements

- Python 3.10 or newer
- A terminal window of at least **120 × 40**
- A terminal with true colour, for the best-looking characters. iTerm2,
  Ghostty, WezTerm and Kitty all work well. macOS Terminal works too, but may
  show faint lines inside the characters.

## Install and run

```sh
git clone https://github.com/chris-basting/celeryman.git
cd celeryman
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install .
celeryman
```

Press **Esc** to quit.

## How to play

Type into the grey bar at the bottom of the **Paul's COMPUTER** window and press
Enter. Talk to it casually: it looks for key words, so "Computer, load up
Celery Man please" works just as well as `celery man`.

To replay the sketch, try these in order:

1. `load up celery man`
2. `kick up the 4d3d3d3`
3. `add sequence: oyster`
4. `print oyster smiling`
5. `any new sequences?`
6. `hat wobble`
7. `flarhgunnstow`
8. `give me 3 taynes`, or `side by side`
9. `nude tayne`, then `y` (don't worry, it's censored)
10. Your wife calls: `hold`
11. Keep going and see what happens. `reset` starts over.

Other commands: `help`, `clear`, `reset`, `quit`.

Drag windows by their title bars, and click **Close** to close them.

## Running the tests

```sh
pip install ".[test]"
pytest
```
