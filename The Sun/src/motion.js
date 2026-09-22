// Keep surface evolution independent of rotation. Cap interrupted frames so
// returning to the scene never causes a sudden spin or eruption jump.
export function advanceMotion(clocks, elapsed, settings, { paused = false, dragging = false } = {}) {
  const delta = paused ? 0 : Math.max(0, Math.min(elapsed, .05));
  return {
    surfaceTime: clocks.surfaceTime + delta * settings.surfaceFlow,
    flareTime: clocks.flareTime + delta * settings.flareActivity,
    coronaTime: clocks.coronaTime + delta,
    rotationStep: dragging ? 0 : delta * .018 * settings.rotation,
  };
}
