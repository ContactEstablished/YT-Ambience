import test from 'node:test';
import assert from 'node:assert/strict';
import {createEruptionEvents,eruptionEnvelope,eruptionParticipation} from './eruption-events.js';

test('flare activity selects more independent event slots, with a smooth partial slot',()=>{
  const total=activity=>Array.from({length:15},(_,i)=>eruptionParticipation(activity,i)).reduce((a,b)=>a+b,0);
  assert.equal(total(0),0);
  assert.equal(total(.1),.5);
  assert.equal(total(1),5);
  assert.equal(total(2),10);
  assert.equal(total(3),15);
});

test('an eruption starts and ends dark, grows rapidly, then fades',()=>{
  const event={start:10,duration:20};
  assert.equal(eruptionEnvelope(event,9).strength,0);
  assert.equal(eruptionEnvelope(event,10).strength,0);
  assert.equal(eruptionEnvelope(event,30).strength,0);
  assert.equal(eruptionEnvelope(event,35).strength,0);
  assert.ok(eruptionEnvelope(event,16).strength>.9);
  assert.ok(eruptionEnvelope(event,28).strength<.2);
  for(let t=10;t<30;t+=.1) assert.ok(eruptionEnvelope(event,t+.1).growth>=eruptionEnvelope(event,t).growth);
});

test('events stay unchanged while animation time is paused',()=>{
  const schedule=createEruptionEvents(42);
  const held=structuredClone(schedule.update(20));
  assert.deepEqual(schedule.update(20),held);
});

test('independent, bounded events include quiet gaps and occasional stronger bursts',()=>{
  const schedule=createEruptionEvents(42);
  const seen=new Map();
  for(let t=0;t<1500;t++) for(const event of schedule.update(t)) seen.set(event.id,event);
  const events=[...seen.values()];
  const violent=events.filter(e=>e.violent);
  assert.ok(violent.length>events.length*.1 && violent.length<events.length*.4);
  assert.equal(new Set(events.map(e=>e.textureSeed)).size,events.length);
  assert.ok(events.some(e=>e.kind==='arch') && events.some(e=>e.kind==='jet'));
  assert.ok(events.every(e=>e.length>=.25 && e.length<=1.1 && e.duration>=11 && e.duration<=28));
  const single=createEruptionEvents(71,1);
  const first=single.events[0];
  const next=single.update(first.start+first.duration)[0];
  assert.ok(next.start>=first.start+first.duration+5);
  assert.equal(eruptionEnvelope(next,first.start+first.duration).strength,0);
});

test('a fixed seed reproduces the GPU test; different seeds vary the scene',()=>{
  const a=createEruptionEvents(51), b=createEruptionEvents(51), c=createEruptionEvents(52);
  for(const t of [0,30,90,200]) assert.deepEqual(a.update(t),b.update(t));
  assert.notDeepEqual(a.update(200),c.update(200));
});
