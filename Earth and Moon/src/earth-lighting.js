const TAU = Math.PI * 2;
export const CYCLE_PHASES = ['Daylight', 'Nightfall', 'Night', 'Dawn'];

export function advanceCycle(turns, rotationRadians) {
  return (turns + rotationRadians / TAU) % CYCLE_PHASES.length;
}

export function getEarthLighting(mode, turns, aspect, shadowDirection, defaultDaylight = 0.8) {
  const cycle = ((turns % 4) + 4) % 4;
  const phase = Math.floor(cycle);
  const progress = cycle - phase;
  const eased = progress * progress * (3 - 2 * progress);
  let sunZ = 2 * defaultDaylight - 1;
  if (mode === 'cycle') {
    const angle = phase === 0 ? 0 : phase === 1 ? Math.PI * eased
      : phase === 2 ? Math.PI : Math.PI * (1 - eased);
    sunZ = Math.cos(angle);
  }
  const x = -shadowDirection.right / aspect, y = shadowDirection.down;
  const scale = Math.sqrt(Math.max(0, 1 - sunZ * sunZ)) / Math.hypot(x, y);
  return {
    sun: [x * scale, y * scale, sunZ],
    daylight: (1 + sunZ) / 2,
    phase: CYCLE_PHASES[phase],
    phaseIndex: phase,
    progress,
  };
}
