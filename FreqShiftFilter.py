import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

fs = 1e6
N = 10000
fA = 200e3
fB = -250e3
noise_level = 0.01

def spectrum(x):
    x = x * np.hanning(N)
    X = np.fft.fft(x)
    power_db = 10 * np.log10(np.abs(X) ** 2 + 1e-12)
    freqs = np.fft.fftfreq(N, d=1 /fs)
    power_db = np.fft.fftshift(power_db)
    freqs = np.fft.fftshift(freqs)
    return freqs, power_db

t = np.arange(N) / fs
x = np.exp(2j * np.pi * fA * t)
x += np.exp(2j * np.pi * fB * t)


if noise_level > 0 :
    noise = noise_level * (np.random.randn(N) + 1j * np.random.randn(N))
    x += noise

y = x * np.exp(-2j * np.pi * fA * t)
taps = signal.firwin(101, 50e3, fs=fs)
w, h = signal.freqz(taps, worN=8192, fs=fs)
h_db = 20 * np.log10(np.abs(h) + 1e-12)

z = signal.lfilter(taps, 1.0, y)

fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(9, 12))

freqs, power_db = spectrum(x)

ax1.plot(freqs / 1e3, power_db)
ax1.axvline(fA / 1e3, color="red", linestyle="--", label=f"tone setting ({fA / 1e3:g} kHz)")
ax1.set_xlabel("Frequency (kHz)", loc="right")
ax1.set_ylabel("Power (dB)")
ax1.set_title("Before")
ax1.legend(loc="upper right")
ax1.grid(True)

freqs, power_db = spectrum(y)

ax2.plot(freqs / 1e3, power_db)
ax2.set_xlabel("Frequency (kHz)", loc="right")
ax2.set_ylabel("Power (dB)")
ax2.set_title("After the shift")
ax2.grid(True)


ax3.plot(w / 1e3, h_db)
ax3.axvline(50, color="red", linestyle="--")
ax3.axvline(-50, color="red", linestyle="--", label="cutoff ±50 kHz")
ax3.axhline(-40, color="gray", linestyle=":", label="−40 dB")
ax3.set_ylim(-110, 5)
ax3.set_xlim(-400, 400)
ax3.set_xlabel("Frequency (kHz)", loc="right")
ax3.set_ylabel("Gain (dB)")
ax3.set_title("Filter response")
ax3.legend(loc="upper right")
ax3.grid(True)

freqs, power_db = spectrum(z)

ax4.plot(freqs / 1e3, power_db)
ax4.set_xlabel("Frequency (kHz)", loc="right")
ax4.set_ylabel("Power (dB)")
ax4.set_title("After filtering")
ax4.grid(True)

plt.tight_layout()
plt.show()
