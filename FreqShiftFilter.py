import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

fs = 1e6
N = 10000
fA = 200e3
fB = -250e3
noise_level = 0.01

def print_spectrum(x):
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

freqs, power_db = print_spectrum(x)
peak = np.argmax(power_db)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6))

n_show = 50
ax1.plot(t[:n_show] * 1e6, x.real[:n_show], label="I (real)")
ax1.plot(t[:n_show] * 1e6, x.imag[:n_show], label="Q (imaginary)")
ax1.set_xlabel("Time (µs)")
ax1.set_ylabel("Amplitude")
ax1.set_title("Signal in time (first 50 samples)")
ax1.legend(loc="upper right")
ax1.grid(True)

ax2.plot(freqs / 1e3, power_db)
ax2.axvline(fA / 1e3, color="red", linestyle="--", label=f"tone setting ({fA / 1e3:g} kHz)")
ax2.set_xlabel("Frequency (kHz)")
ax2.set_ylabel("Power (dB)")
ax2.set_title("Spectrum")
ax2.legend(loc="upper right")
ax2.grid(True)


plt.tight_layout()
plt.show()
