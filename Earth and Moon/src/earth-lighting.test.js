import test from 'node:test';
import assert from 'node:assert/strict';
import { advanceCycle, getEarthLighting } from './earth-lighting.js';

const direction = { down: 0.62, right: 0.38 };
const sample = (turns, mode = 'cycle', aspect = 2) => getEarthLighting(mode, turns, aspect, direction);

test('holds daylight and night for one full rotation each', () => {
  for (const turn of [0, 0.25, 0.5, 0.999999]) assert.equal(sample(turn).daylight, 1);
  for (const turn of [2, 2.25, 2.5, 2.999999]) assert.equal(sample(turn).daylight, 0);
});

test('nightfall advances monotonically and all four boundaries are continuous', () => {
  let previous = 1;
  for (let turn = 1; turn < 2; turn += 0.01) {
    const current = sample(turn).daylight;
    assert.ok(current <= previous);
    previous = current;
  }
  for (const boundary of [1, 2, 3, 4]) {
    assert.ok(Math.abs(sample(boundary - 0.00001).daylight - sample(boundary + 0.00001).daylight) < 1e-8);
  }
  assert.ok(Math.abs(sample(1.5).daylight - 0.5) < 1e-12);
  assert.ok(Math.abs(sample(3.5).daylight - 0.5) < 1e-12);
});

test('timing counts actual rotation at all speeds; zero motion holds the phase', () => {
  for (const speed of [0.05, 1, 20]) {
    const secondsPerTurn = Math.PI * 2 / (0.018 * speed);
    const turns = advanceCycle(0, 0.018 * speed * secondsPerTurn);
    assert.ok(Math.abs(turns - 1) < 1e-12);
  }
  assert.equal(advanceCycle(2.4, 0), 2.4);
  assert.equal(advanceCycle(3, Math.PI * 2), 0);
});

test('Default preserves 80% daylight and the Moon-aligned angle at every aspect', () => {
  for (const aspect of [0.6, 1, 2.4]) {
    for (const turns of [0, 1.5, 2.8, 9]) {
      const value = sample(turns, 'default', aspect);
      assert.equal(value.daylight, 0.8);
      assert.ok(Math.abs(Math.hypot(...value.sun) - 1) < 1e-12);
      assert.ok(Math.abs(value.sun[0] / value.sun[1] + direction.right / (aspect * direction.down)) < 1e-12);
    }
  }
});
