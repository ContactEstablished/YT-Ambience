// Match Earth's four-rotation ambience cycle. Lighting is relative to the
// fixed camera, so the percentage describes the projected disk in shadow.
const TAU = Math.PI * 2;
export const CYCLE_PHASES = ['Daylight', 'Nightfall', 'Night', 'Dawn'];
export const DEFAULT_SHADOW = 20;

export function advanceCycle(turns, rotationRadians) {
  return (turns + rotationRadians / TAU) % CYCLE_PHASES.length;
}

export function getMarsLighting(mode, turns, shadowPercent = DEFAULT_SHADOW) {
  const cycle = ((turns % 4) + 4) % 4;
  const phaseIndex = Math.floor(cycle);
  const progress = cycle - phaseIndex;
  const eased = progress * progress * (3 - 2 * progress);
  let sunZ = 1 - 2 * Math.max(0, Math.min(100, shadowPercent)) / 100;
  if (mode === 'cycle') {
    const angle = phaseIndex === 0 ? 0 : phaseIndex === 1 ? Math.PI * eased
      : phaseIndex === 2 ? Math.PI : Math.PI * (1 - eased);
    sunZ = Math.cos(angle);
  }
  const sunXY = Math.sqrt(Math.max(0, 1 - sunZ * sunZ));
  // A light directly behind the mesh can leave tiny grazing highlights along
  // its silhouette. Ease it out over the final 1% of shadow, leaving the
  // material's night-visibility floor to reveal the terrain at full night.
  const nightFade = Math.min(1, Math.max(0, (1 + sunZ) / 0.02));
  return {
    sun: [-sunXY * 0.8, sunXY * 0.6, sunZ],
    sunlightStrength: nightFade * nightFade * (3 - 2 * nightFade),
    shadowPercent: (1 - sunZ) * 50,
    phase: CYCLE_PHASES[phaseIndex],
    phaseIndex,
    progress,
  };
}
