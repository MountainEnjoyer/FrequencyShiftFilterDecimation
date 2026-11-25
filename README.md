# FrequencyShiftFilterDecimation

A Python script that isolates one signal from a slice of spectrum and reduces its sample rate: it moves the wanted signal to 0 Hz, removes its neighbour with a low-pass filter, then keeps only one sample in ten. A second, unfiltered decimation runs alongside it to show what happens when the filter is skipped: the neighbour folds back on top of the signal.

It is the third and last exercise of the DSP fundamentals phase of a larger project: a multi-mode software-defined radio (SDR) decoder that turns signals received with an RTL-SDR dongle into sound and decoded data. Shift, filter, decimate is the front end of every channel that decoder will tune. Here it is built and checked on synthetic signals, where the right answer is known in advance.

It continues the previous exercises: [FreqFinder](https://github.com/MountainEnjoyer/FreqFinder) (the spectrum tool) and [FrequencyShiftFilter](https://github.com/MountainEnjoyer/FrequencyShiftFilter) (the shift and the filter).

## Why this exists

After filtering, the wanted signal only occupies ±50 kHz, but it is still described by 1 million samples per second. Keeping every tenth sample (**decimation**) describes it just as well with 100,000 samples per second, and makes every later stage of a decoder ten times cheaper.

The catch is that the new sample rate can only represent frequencies between −50 and +50 kHz. Anything outside that range does not disappear: it **aliases**, folding back to a false frequency inside it. Once folded on top of the wanted signal, it can never be separated again. That is why the order is always:

1. **Shift** the wanted signal to 0 Hz.
2. **Filter** away everything outside the band to keep.
3. **Decimate**.

This script shows the right order and the wrong one side by side.

## Repository contents

```
FrequencyShiftFilterDecimation/
├── FreqShiftFilter.py   # the script: signal generation, shift, filter, decimation, plots
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
git clone https://github.com/MountainEnjoyer/FrequencyShiftFilterDecimation.git
cd FrequencyShiftFilterDecimation
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

`exec.sh` activates the virtual environment in `.venv` and runs `FreqShiftFilter.py` with the environment's Python. It uses paths relative to the repository, so run it from inside the `FrequencyShiftFilterDecimation` folder.

To run the script manually instead:

```bash
source .venv/bin/activate
python FreqShiftFilter.py
deactivate
```

The script prints nothing; it opens a window with five plots stacked from top to bottom.

### What the five plots show (default settings)

| Plot | Range | What you see |
| --- | --- | --- |
| **Before** | ±500 kHz | Two peaks of about 74 dB: the signal to keep at +200 kHz (marked by the red dashed line) and the neighbour at +120 kHz. |
| **After the shift** | ±500 kHz | Everything has moved 200 kHz to the left: the signal now sits at 0 Hz and the neighbour at −80 kHz. |
| **Filter response** | ±500 kHz | The low-pass filter: 0 dB around 0 Hz, −6 dB at the ±50 kHz cutoff (red dashed lines), below −40 dB (grey dotted line) from about ±65 kHz. |
| **Filtering and decimation** | ±50 kHz | The right order. One clean peak at 0 Hz, about 54 dB, over a noise floor near −23 dB. The neighbour was removed before decimation, so nothing folds in. |
| **Decimation without filtering** | ±50 kHz | The wrong order. The neighbour has folded from −80 kHz to **+20 kHz** (red dashed line), as loud as the signal at about 54 dB. The noise floor is 10 dB higher, near −13 dB, because the noise of the whole ±500 kHz band folded in too. |

The two decimated spectra have 1,000 samples instead of 10,000, so a full tone reaches 60 dB instead of 80 dB, and the Hann window used for display lowers both by 6 dB: 74 dB before decimation, 54 dB after. The signal is not weaker; there are fewer samples. Levels are relative, not calibrated, and noise values change slightly on every run.

## Configuration

All settings are at the top of `FreqShiftFilter.py`.

| Setting | Default | Description |
| --- | --- | --- |
| `fs` | `1e6` | Sample rate before decimation, in samples per second. The first three plots cover −500 to +500 kHz. |
| `N` | `10000` | Number of samples, giving 100 Hz frequency bins. |
| `fA` | `200e3` | Frequency of the signal to keep, in Hz. The shift always moves `fA` to 0 Hz. |
| `fB` | `120e3` | Frequency of the neighbour, in Hz. After the shift it sits at `fB − fA`. |
| `num_taps` | `101` | Number of filter coefficients. More taps give a sharper filter edge. |
| `noise_level` | `0.01` | Standard deviation of the complex Gaussian noise. `0` gives a clean signal. |

Two more values are set in the code: the filter cutoff (50 kHz) in the call to `signal.firwin`, and the decimation factor (10), in the two `[::10]` slices and in `fs_dec = fs / 10`. When changing the factor, change all three places together.

## How it works

### 1. Signal

Two complex tones, `exp(j·2π·fA·t)` and `exp(j·2π·fB·t)`, are added together with optional complex noise. This imitates a slice of spectrum as an SDR delivers it, as I/Q samples, with two signals in it.

### 2. Frequency shift

```python
y = x * np.exp(-2j * np.pi * fA * t)
```

Multiplying two complex numbers adds their angles, so multiplying every sample by a tone rotating at −fA lowers every frequency by fA. The signal at fA lands at 0 Hz, the neighbour at fB − fA = −80 kHz.

### 3. Low-pass filter

```python
taps = signal.firwin(num_taps, 50e3, fs=fs)
z = signal.lfilter(taps, 1.0, y)
```

`firwin` designs a low-pass FIR filter that keeps ±50 kHz around 0 Hz; `lfilter` applies it to every sample. `signal.freqz` computes its response for the third plot, over the full ±500 kHz.

### 4. Decimation

```python
z_dec = z[num_taps:][::10]
fs_dec = fs / 10
```

`z[num_taps:]` drops the filter's start-up transient (its first outputs, computed while its memory was still empty). `[::10]` then keeps every tenth sample. The sample rate drops to 100,000 samples per second, so the visible range becomes ±50 kHz, exactly the band the filter kept.

### 5. Decimation without filtering

```python
y_dec = y[::10]
```

The same decimation applied to the shifted but unfiltered signal, for comparison.

### 6. Spectrum

The `spectrum(x, fs)` function applies a Hann window, computes the FFT, converts it to power in dB and reorders it from −fs/2 to +fs/2. It takes the sample rate as a parameter, so the same function labels the frequencies correctly before (`fs`) and after (`fs_dec`) decimation.

## Why the neighbour lands at +20 kHz

At 100,000 samples per second, a tone at −80 kHz turns −0.8 of a full circle between one sample and the next. Since whole turns are invisible in the samples, that lands in exactly the same places as turning +0.2 of a circle, which is a tone at +20 kHz:

```
e^(j·2π·(−0.8)·n) = e^(j·2π·(+0.2)·n)    for every whole number n
```

In general, a frequency outside ±fs_dec/2 is moved by multiples of fs_dec until it falls inside: −80 kHz + 100 kHz = +20 kHz. Before decimation, at 1 million samples per second, the same tone turns only −0.08 of a circle per sample, which is unambiguous, so the filter can recognise it and remove it.

## Experiments

Change one setting at a time and predict the result before running. The results below were produced by this script.

| Change | Filtering and decimation | Decimation without filtering | Concept |
| --- | --- | --- | --- |
| Default | Nothing at +20 kHz (about −14 dB) | Neighbour at +20 kHz, 54 dB | **Filter before decimating.** |
| `num_taps = 21` | Neighbour at +20 kHz, 41 dB: only 13 dB below the signal | Neighbour at +20 kHz, 54 dB | **A weak filter leaks.** What the filter fails to remove still folds in, and stays. |
| `fB = 170e3` (neighbour lands at −30 kHz) | Neighbour stays at −30 kHz, 54 dB | Neighbour stays at −30 kHz, 54 dB | **In-band signals.** A neighbour inside the kept band is not aliasing, and no decimation can remove it: the filter has to be narrower. |
| `fB = -250e3` (neighbour lands at −450 kHz) | Nothing at the folded position (about −40 dB) | Neighbour folded to −50 kHz, 54 dB | **Every out-of-band signal folds somewhere**, even a distant one: −450 kHz + 4 × 100 kHz = −50 kHz, the edge of the range. |

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `.venv/bin/activate: No such file or directory` | The virtual environment was not created, or `exec.sh` was run from another folder | Create it (Installation, step 3) and run `./exec.sh` from inside `FrequencyShiftFilterDecimation`. |
| `ModuleNotFoundError: No module named 'scipy'` | SciPy is missing from the virtual environment | `source .venv/bin/activate`, then `pip install scipy`. |
| `error: externally-managed-environment` | `pip install` was run outside the virtual environment | Activate `.venv` before installing. |
| `Permission denied` when running `./exec.sh` | The launcher is not executable | `chmod +x exec.sh` |
| No plot window appears | The `tk` package is missing, or Matplotlib is using a non-interactive backend | `sudo pacman -S tk`, and run from a regular terminal. |
| The folded neighbour appears at +200 kHz instead of +20 kHz (after editing) | A decimated signal was passed to `spectrum()` with `fs` instead of `fs_dec` | Always pass the rate the signal actually has. |
| Peaks in the wrong place after changing the decimation factor | The factor was changed in one place but not the others | Change both `[::10]` slices and `fs_dec` together. |
| Errors after a system Python upgrade | The virtual environment was built for the previous Python version | `rm -rf .venv`, then repeat Installation, step 3. |

## Roadmap

This repository completes the DSP fundamentals phase:

1. [FreqFinder](https://github.com/MountainEnjoyer/FreqFinder): find a frequency with the FFT.
2. [FrequencyShiftFilter](https://github.com/MountainEnjoyer/FrequencyShiftFilter): shift a signal to 0 Hz and isolate it with a low-pass filter.
3. **FrequencyShiftFilterDecimation (this repository):** reduce the sample rate, and see why the filter must come first.

The next phase records a real FM station with an RTL-SDR and runs it through this same chain, adding FM demodulation to turn it into sound.

## Further reading

- [PySDR: A Guide to SDR and DSP using Python](https://pysdr.org), chapters on sampling, filters and multi-rate processing
- [SciPy signal processing documentation](https://docs.scipy.org/doc/scipy/reference/signal.html): `firwin`, `freqz`, `lfilter`, `decimate`
