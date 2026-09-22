import test from 'node:test';
import assert from 'node:assert/strict';
import { advanceMotion } from './motion.js';

const clocks = {surfaceTime: 2,flareTime: 3,coronaTime: 4};
const settings = {rotation: 1,surfaceFlow: 1,flareActivity: 1,sunspots: 1};
test('zero rotation leaves surface and flares evolving independently',()=>{
  assert.deepEqual(advanceMotion(clocks,.04,{...settings,rotation:0,surfaceFlow:3,flareActivity:2}),
    {surfaceTime:2.12,flareTime:3.08,coronaTime:4.04,rotationStep:0});
});
test('zero surface flow freezes only the surface',()=>{
  const state=advanceMotion(clocks,.04,{...settings,surfaceFlow:0,rotation:20});
  assert.equal(state.surfaceTime,2);
  assert.equal(state.flareTime,3.04);
  assert.equal(state.coronaTime,4.04);
  assert.ok(Math.abs(state.rotationStep-.0144)<1e-12);
});
test('zero flare activity freezes only the flare clock',()=>{
  const state=advanceMotion(clocks,.04,{...settings,flareActivity:0});
  assert.equal(state.flareTime,3);
  assert.equal(state.surfaceTime,2.04);
  assert.equal(state.coronaTime,4.04);
});
test('sunspot amount never changes motion or event timing',()=>{
  assert.deepEqual(advanceMotion(clocks,.04,{...settings,sunspots:0}),advanceMotion(clocks,.04,{...settings,sunspots:3}));
});
test('pause holds every clock; dragging only holds rotation',()=>{
  assert.deepEqual(advanceMotion(clocks,.04,settings,{paused:true}),{...clocks,rotationStep:0});
  assert.deepEqual(advanceMotion(clocks,.04,settings,{dragging:true}),{surfaceTime:2.04,flareTime:3.04,coronaTime:4.04,rotationStep:0});
});
test('interrupted frames cannot jump or rewind any animation clock',()=>{
  assert.deepEqual(advanceMotion(clocks,60,settings),advanceMotion(clocks,.05,settings));
  assert.deepEqual(advanceMotion(clocks,-1,settings),{...clocks,rotationStep:0});
});
