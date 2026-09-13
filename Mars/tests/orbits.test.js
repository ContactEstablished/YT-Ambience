import test from 'node:test';
import assert from 'node:assert/strict';
import { MOONS, moonDisplay, orbitPose, surfacePosition, systemHalfHeight } from '../src/orbits.js';

const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);

test('moons complete an orbit without intersecting Mars or each other', () => {
  for (let time = 0; time <= 720; time += 0.5) {
    const positions = MOONS.map(moon => {
      const pose = orbitPose(moon, time);
      near(Math.hypot(...pose.position), moon.radius);
      assert.ok(moon.radius - moon.diameter / 2 > 1);
      // Local -X stays pointed at the planet throughout the orbit.
      near(-Math.cos(pose.rotationY), -pose.position[0] / moon.radius);
      near(Math.sin(pose.rotationY), -pose.position[2] / moon.radius);
      return pose.position;
    });
    const separation = Math.hypot(...positions[0].map((v, i) => v - positions[1][i]));
    assert.ok(separation > (MOONS[0].diameter + MOONS[1].diameter) / 2);
  }
  for (const moon of MOONS) {
    orbitPose(moon, moon.period).position.forEach((v, i) => near(v, orbitPose(moon, 0).position[i]));
  }
  assert.ok(MOONS[0].period < MOONS[1].period);
});

test('default framing contains full orbits in portrait, square, and landscape', () => {
  const extent = Math.max(...MOONS.map(moon => moon.radius + moon.diameter / 2));
  for (const aspect of [320 / 740, 390 / 844, 1, 16 / 9, 21 / 9]) {
    const halfHeight = systemHalfHeight(aspect);
    assert.ok(halfHeight > extent);
    assert.ok(halfHeight * aspect > extent);
  }
});

test('true scale uses physical dimensions and center distances without changing orbital phase or timing', () => {
  const lengths = [27, 15], distances = [9375, 23457];
  MOONS.forEach((moon, i) => {
    const actual = moonDisplay(moon, 'true');
    near(actual.diameter * 3390, lengths[i]);
    near(actual.radius * 3390, distances[i]);
    assert.equal(actual.period, moon.period);
    for (const time of [0, 45, 180, 720]) {
      const a = orbitPose(actual, time), b = orbitPose(moon, time);
      near(a.rotationY, b.rotationY);
      a.position.forEach((v, axis) => near(v / actual.radius, b.position[axis] / moon.radius));
    }
    assert.ok(actual.radius + actual.diameter / 2 < 7.5);
  });
});

test('latitude/longitude placement matches a north-up, east-positive cylindrical Mars texture', () => {
  const cases = [[0, 0, [1, 0, 0]], [0, 90, [0, 0, -1]], [90, 0, [0, 1, 0]], [-90, 0, [0, -1, 0]], [0, 180, [-1, 0, 0]]];
  for (const [lat, lon, expected] of cases) surfacePosition(lat, lon, 1).forEach((v, axis) => near(v, expected[axis]));
  surfacePosition(18.65, 226.2, 1).forEach((v, axis) => near(v, surfacePosition(18.65, -133.8, 1)[axis]));
});
