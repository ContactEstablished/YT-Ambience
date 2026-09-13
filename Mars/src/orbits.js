// Artistic scene units: Mars radius = 1. Sizes and distances are intentionally
// exaggerated/compressed for an ambience composition, not an ephemeris.
export const MOONS = [
  { name: 'phobos', diameter: 0.25, radius: 1.6, period: 180, phase: 0.30, lengthKm: 27, orbitKm: 9375 },
  { name: 'deimos', diameter: 0.16, radius: 2.3, period: 720, phase: Math.PI + 0.25, lengthKm: 15, orbitKm: 23457 },
];

export const MARS_RADIUS_KM = 3390;

export function moonDisplay(moon, mode = 'illustrated') {
  return mode === 'true' ? { ...moon, diameter: moon.lengthKm / MARS_RADIUS_KM, radius: moon.orbitKm / MARS_RADIUS_KM } : moon;
}

// A -180..180 east-positive, north-up cylindrical texture on SphereGeometry.
export function surfacePosition(latitude, longitude, radius = 1.006) {
  const lat = latitude * Math.PI / 180, lon = longitude * Math.PI / 180;
  return [radius * Math.cos(lat) * Math.cos(lon), radius * Math.sin(lat), -radius * Math.cos(lat) * Math.sin(lon)];
}

export function orbitPose(moon, elapsedSeconds) {
  const angle = moon.phase + (elapsedSeconds % moon.period) / moon.period * Math.PI * 2;
  return {
    position: [moon.radius * Math.cos(angle), 0, -moon.radius * Math.sin(angle)],
    rotationY: angle,
  };
}

export function systemHalfHeight(aspect, halfFrame = 2.7) {
  return halfFrame / Math.min(1, Math.max(0.01, aspect));
}
