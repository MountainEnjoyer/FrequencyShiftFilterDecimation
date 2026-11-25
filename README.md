# FrequencyShiftFilter

A Python script that takes a slice of spectrum containing two signals, moves the one you want to 0 Hz, and removes the other with a digital low-pass filter.

It is the second exercise of a larger project: a multi-mode software-defined radio (SDR) decoder that turns signals received with an RTL-SDR dongle into sound and decoded data. These are the first two stages of every channel the decoder will tune: **shift** the wanted station to the center, then **filter** away everything around it. Here they are built and checked on synthetic signals, where the right answer is known in advance.

The previous exercise, [FreqFinder](https://github.com/MountainEnjoyer/FreqFinder), builds the spectrum tool this one relies on.

## Why this exists

An SDR does not deliver one station: it delivers a whole slice of spectrum, often 2.4 MHz wide, with many signals in it. Before a station can be demodulated, it has to be isolated:

1. **Shift.** Multiplying the samples by a rotating complex tone slides the whole spectrum sideways, so the wanted station sits at 0 Hz.
2. **Filter.** A low-pass filter keeps a narrow band around 0 Hz and removes the neighbouring signals and the noise outside it.

The order matters: the filter only keeps what is near 0 Hz, so the station has to be moved there first. This script shows each step on its own plot, so you can follow both signals through the chain.

## Repository contents

```
FrequencyShiftFilter/
├── FreqShiftFilter.py   # the script: signal generation, shift, filter, plots
├── exec.sh              # launcher: activates the virtual environment and runs the script
└── README.md
```

The virtual environment (`.venv/`) is created locally during installation and is not part of the repository.

## Requirements

- Linux (developed and tested on Arch Linux)
- Python 3.8 or later
- [NumPy](https://numpy.org), [SciPy](https://scipy.org) and [Matplotlib](https://matplotlib.org), installed in a virtual environment
- Tk, for the plot window (Matplotlib's default interactive backend)

No radio hardware is needed.

## Installation (Arch Linux)

### 1. Install the system packages

```bash
sudo pacman -S --needed python tk git
```

`python` provides the interpreter and the `venv` module. `tk` provides the graphics library Matplotlib uses to open its plot window; without it the script runs but no window appears.

### 2. Clone the repository

```bash
git clone https://github.com/MountainEnjoyer/FrequencyShiftFilter.git
cd FrequencyShiftFilter
```

### 3. Create the virtual environment and install the dependencies

Arch marks its system Python as externally managed ([PEP 668](https://peps.python.org/pep-0668/)), so `pip install` outside a virtual environment is refused with an `externally-managed-environment` error. The dependencies therefore live in a local `.venv` folder.

```bash
python -m venv .venv
source .venv/bin/activate
pip install numpy scipy matplotlib
deactivate
```

This only needs to be done once.

## Usage

From the repository folder:

```bash
./exec.sh
```

`exec.sh` activates the virtual environment in `.venv` and runs `FreqShiftFilter.py` with the environment's Python. It uses paths relative to the repository, so run it from inside the `FrequencyShiftFilter` folder.

To run the script manually instead:

```bash
source .venv/bin/activate
python FreqShiftFilter.py
deactivate
```

The script prints nothing; it opens a window with four plots stacked from top to bottom.

### What the four plots show (default settings)

| Plot | What you see |
| --- | --- |
| **Before** | Two peaks of about 74 dB: the station at +200 kHz (marked by the red dashed line) and the neighbour at +120 kHz, over a noise floor near 0 dB. |
| **After the shift** | Everything has moved 200 kHz to the left: the station now sits at 0 Hz and the neighbour at −80 kHz. |
| **Filter response** | The filter's gain at each frequency: flat at 0 dB around 0 Hz, −6 dB at the ±50 kHz cutoff (red dashed lines), and below −40 dB (grey dotted line) from about ±65 kHz. |
| **After filtering** | The station is unchanged at 0 Hz, about 74 dB. The neighbour has dropped to about 5 dB, 69 dB below the station, and the noise outside ±50 kHz has fallen to around −80 dB. |

Levels are relative, not calibrated: a full-amplitude tone over N = 10,000 samples would reach 80 dB, and the Hann window used for display lowers it by 6 dB. Noise is random, so small values change slightly on every run.

## Configuration

All settings are at the top of `FreqShiftFilter.py`.

| Setting | Default | Description |
| --- | --- | --- |
| `fs` | `1e6` | Sample rate in samples per second. The spectrum covers −500 to +500 kHz. |
| `N` | `10000` | Number of samples, giving 100 Hz frequency bins. |
| `fA` | `200e3` | Frequency of the station, the signal to keep, in Hz. The shift always moves `fA` to 0 Hz. |
| `fB` | `120e3` | Frequency of the neighbour, the signal to remove, in Hz. |
| `num_taps` | `101` | Number of filter coefficients. More taps give a sharper filter edge, at the cost of more computation and more delay. |
| `noise_level` | `0.01` | Standard deviation of the complex Gaussian noise added to the signal. `0` gives a clean signal. |

The filter cutoff (50 kHz) is set directly in the call to `signal.firwin`.

## How it works

### 1. Signal

Two complex tones, `exp(j·2π·fA·t)` and `exp(j·2π·fB·t)`, are added together with optional complex noise. This imitates a slice of spectrum as an SDR delivers it, as I/Q samples, with two stations in it.

### 2. Frequency shift

```python
y = x * np.exp(-2j * np.pi * fA * t)
```

Multiplying two complex numbers adds their angles, so multiplying every sample by a tone rotating at −fA lowers every frequency in the signal by fA. The station at fA lands at 0 Hz and the neighbour at fB − fA. Nothing is removed yet: both signals are still there, just moved.

### 3. Filter design

```python
taps = signal.firwin(num_taps, 50e3, fs=fs)
```

`firwin` designs a low-pass FIR (finite impulse response) filter: a list of `num_taps` weights. Applying it replaces each sample by a weighted sum of the last `num_taps` samples, which keeps slow changes (low frequencies) and cancels fast ones (high frequencies). The cutoff is 50 kHz, so the filter passes a band from −50 to +50 kHz.

### 4. Filter response

`signal.freqz` computes the filter's gain at 8192 frequencies. With `whole=True` it covers 0 to fs; the upper half is relabelled as negative frequencies and reordered with `fftshift`, so the response is drawn from −500 to +500 kHz like the spectra.

### 5. Filtering

```python
z = signal.lfilter(taps, 1.0, y)
```

`lfilter` applies the filter to every sample. The `1.0` means there is no feedback (an FIR filter).

### 6. Start-up transient

The filter's memory starts empty, so its first `num_taps` outputs are not valid yet. They are left out of the last spectrum with `z[num_taps:]`.

### 7. Spectrum

The `spectrum()` function applies a Hann window, computes the FFT, converts it to power in dB and reorders it from −fs/2 to +fs/2. It uses the length of whatever it receives, so it works on both the full signal and the trimmed filter output.

## Experiments

Change one setting at a time and predict the result before running. The results below were produced by this script.

| Change | Result | Concept |
| --- | --- | --- |
| Default (`num_taps = 101`, neighbour lands at −80 kHz) | Neighbour 69 dB below the station | **Close neighbour.** Only 30 kHz outside the passband, it still needs a sharp filter. |
| `num_taps = 21` | Neighbour only 13 dB below the station; the filter reaches −40 dB only at 126 kHz | **Filter length.** Fewer taps give a gradual edge: the neighbour stays almost as loud as the station. |
| `num_taps = 301` | −40 dB reached at 55 kHz; neighbour 64 dB below the station | **Sharper is not always deeper.** More taps narrow the edge, but the rejection beyond it is set by the filter's window design, not by its length. |
| `fB = -250e3` | Neighbour lands at −450 kHz and ends 83 dB below the station | **Distant neighbour.** Far outside the passband, it is removed easily. |
| Shift with the wrong sign: `np.exp(2j * np.pi * fA * t)` | Station moves to +400 kHz and neighbour to +320 kHz; after filtering, only noise is left | **Shift direction.** Moving the wrong way pushes the station out of the passband. |
| Skip the shift (filter `x` directly) | Both signals are outside ±50 kHz and are removed | **Shift before filtering.** The filter only keeps what sits near 0 Hz. |

### Filter length at a glance

| `num_taps` | −6 dB point | Below −40 dB from | Delay |
| --- | --- | --- | --- |
| 21 | 57 kHz | 126 kHz | 10 samples (10 µs) |
| 101 | 50 kHz | 65 kHz | 50 samples (50 µs) |
| 301 | 50 kHz | 55 kHz | 150 samples (150 µs) |

A linear-phase FIR filter delays the signal by (num_taps − 1) / 2 samples.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `.venv/bin/activate: No such file or directory` | The virtual environment was not created, or `exec.sh` was run from another folder | Create it (Installation, step 3) and run `./exec.sh` from inside `FrequencyShiftFilter`. |
| `ModuleNotFoundError: No module named 'scipy'` | SciPy is missing from the virtual environment | `source .venv/bin/activate`, then `pip install scipy`. |
| `error: externally-managed-environment` | `pip install` was run outside the virtual environment | Activate `.venv` before installing. |
| `Permission denied` when running `./exec.sh` | The launcher is not executable | `chmod +x exec.sh` |
| No plot window appears | The `tk` package is missing, or Matplotlib is using a non-interactive backend | `sudo pacman -S tk`, and run from a regular terminal. |
| `ValueError` from `firwin` (after editing) | The cutoff was given without `fs=fs`, so it is read as a fraction of fs/2 | Keep `fs=fs` in the call. |
| `operands could not be broadcast together` (after editing) | The spectrum function was given an array whose length differs from the window's | Keep `n = len(x)` inside `spectrum()`. |
| Errors after a system Python upgrade | The virtual environment was built for the previous Python version | `rm -rf .venv`, then repeat Installation, step 3. |

## Roadmap

FrequencyShiftFilter covers the second exercise of the DSP fundamentals phase:

1. [FreqFinder](https://github.com/MountainEnjoyer/FreqFinder): find a frequency with the FFT.
2. **FrequencyShiftFilter (this repository):** shift a signal to 0 Hz and isolate it with a low-pass filter.
3. Decimate with and without filtering to observe aliasing.

Later phases decode real signals from an RTL-SDR: FM and AM radio, then digital modes such as ADS-B aircraft messages.

## Further reading

- [PySDR: A Guide to SDR and DSP using Python](https://pysdr.org), chapters on filters and frequency shifting
- [SciPy signal processing documentation](https://docs.scipy.org/doc/scipy/reference/signal.html): `firwin`, `freqz`, `lfilter`
