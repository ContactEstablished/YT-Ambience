import test from 'node:test';
import assert from 'node:assert/strict';
import { advanceCycle, getMarsLighting } from '../src/lighting.js';

const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-10, `${a} != ${b}`);

test('static shadow covers 0–100% of the disk and preserves the original default lighting', () => {
  for (const percent of [0, 20, 50, 75, 100]) {
    for (const turn of [0, 1.5, 2.5, 4]) {
      const state = getMarsLighting('static', turn, percent);
      near(state.shadowPercent, percent);
      near(Math.hypot(...state.sun), 1);
      near(state.sun[2], 1 - 2 * percent / 100);
    }
  }
  getMarsLighting('static', 0).sun.forEach((value, index) => near(value, [-0.64, 0.48, 0.6][index]));
});

test('cycle holds day and night for one rotation each, regardless of saved static shadow', () => {
  for (const shadow of [0, 20, 100]) {
    for (const turns of [0, 0.5, 0.999999]) near(getMarsLighting('cycle', turns, shadow).shadowPercent, 0);
    for (const turns of [2, 2.5, 2.999999]) near(getMarsLighting('cycle', turns, shadow).shadowPercent, 100);
  }
});

test('nightfall and dawn are smooth, monotonic, and continuous through loop boundaries', () => {
  let previous = 0;
  for (let turns = 1; turns <= 2; turns += 0.01) {
    const state = getMarsLighting('cycle', turns);
    assert.ok(state.shadowPercent >= previous);
    near(getMarsLighting('cycle', turns + 2).shadowPercent, 100 - state.shadowPercent);
    near(Math.hypot(...state.sun), 1);
    previous = state.shadowPercent;
  }
  for (const boundary of [1, 2, 3, 4]) {
    const a = getMarsLighting('cycle', boundary - 1e-6);
    const b = getMarsLighting('cycle', boundary + 1e-6);
    near(a.shadowPercent, b.shadowPercent);
    a.sun.forEach((v, i) => near(v, b.sun[i]));
  }
  near(getMarsLighting('cycle', 1.5).shadowPercent, 50);
  near(getMarsLighting('cycle', 3.5).shadowPercent, 50);
  assert.equal(getMarsLighting('cycle', 4).phase, 'Daylight');
});

test('loop follows actual Mars rotation; zero rotation holds the phase and four turns wrap', () => {
  for (const speed of [0.05, 1, 20]) {
    const seconds = Math.PI * 2 / (0.012 * speed);
    near(advanceCycle(0, 0.012 * speed * seconds), 1);
  }
  assert.equal(advanceCycle(1.5, 0), 1.5);
  assert.equal(advanceCycle(3, Math.PI * 2), 0);
});

test('full night removes rim-producing sunlight and restores it smoothly at dawn', () => {
  for (const percent of [0, 20, 50, 99]) near(getMarsLighting('static', 0, percent).sunlightStrength, 1);
  near(getMarsLighting('static', 0, 100).sunlightStrength, 0);
  let previous = 1;
  for (let percent = 99; percent <= 100; percent += 0.01) {
    const strength = getMarsLighting('static', 0, percent).sunlightStrength;
    assert.ok(strength >= 0 && strength <= previous);
    previous = strength;
  }
  for (const turn of [2, 2.5, 2.999999]) near(getMarsLighting('cycle', turn).sunlightStrength, 0);
  for (const turn of [1.8, 1.9, 1.99, 2]) {
    near(getMarsLighting('cycle', turn).sunlightStrength, getMarsLighting('cycle', 5 - turn).sunlightStrength);
  }
  near(getMarsLighting('cycle', 4).sunlightStrength, 1);
});
