/** Measures the actual input waveform. This detects sound, not speech or emotion. */
export function measureAudio(samples: ArrayLike<number>) {
  let squareSum = 0;
  for (let i = 0; i < samples.length; i++) squareSum += samples[i] * samples[i];
  const rms = samples.length ? Math.sqrt(squareSum / samples.length) : 0;
  const db = rms > 0 ? 20 * Math.log10(rms) : -100;
  return {rms, db, level: Math.max(0, Math.min(1, (db + 80) / 68))};
}
