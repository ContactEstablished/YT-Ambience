// Seeded for repeatable GPU tests; the live scene supplies a new seed per load.
export function eruptionParticipation(activity,slot) {
  return Math.max(0,Math.min(1,activity*5-slot));
}

export function createEruptionEvents(seed, count = 5) {
  let state = seed >>> 0;
  const random = () => { state = (1664525 * state + 1013904223) >>> 0; return state / 4294967296; };
  let serial = 0;
  function create(start) {
    const violent = random() < .26;
    return {
      id: serial++, start, duration: 11 + random()*17,
      violent, kind: random() < .4 ? 'arch' : 'jet',
      longitude: random()*Math.PI*2, latitude: (random()-.5)*1.8,
      roll: random()*Math.PI*2,
      length: violent ? .65+random()*.45 : .25+random()*.35,
      width: violent ? .15+random()*.13 : .055+random()*.085,
      span: .13+random()*.23, bend: (random()-.5)*.7,
      twist: (random()-.5)*2.4, textureSeed: random()*100,
      power: violent ? 1.2+random()*.7 : .65+random()*.5,
    };
  }
  // Start with a little ongoing activity; later events have independent quiet gaps.
  const events = Array.from({length: count},(_,i)=>create(i < 2 ? -4-i*3 : 3+random()*22));
  return {
    events,
    update(time) {
      for (let i=0;i<events.length;i++) {
        while (time >= events[i].start+events[i].duration) {
          const nextStart = events[i].start+events[i].duration+5+random()*24;
          events[i] = create(nextStart);
        }
      }
      return events;
    },
  };
}

export function eruptionEnvelope(event,time) {
  const age = Math.max(0,Math.min(1,(time-event.start)/event.duration));
  const smooth = x => { x = Math.max(0,Math.min(1,x)); return x*x*(3-2*x); };
  return {
    age,
    // Rapid launch, a sustained middle, then a long fade. Both endpoints are zero.
    strength: smooth(age/.12)*(1-smooth((age-.48)/.52)),
    growth: .16+.84*(1-(1-age)**3),
  };
}
