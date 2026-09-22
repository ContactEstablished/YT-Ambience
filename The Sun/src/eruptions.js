import * as THREE from 'three';
import { createEruptionEvents, eruptionEnvelope, eruptionParticipation } from './eruption-events.js';

export function createEruptions(shared,noise,seed) {
  const group = new THREE.Group();
  const schedule = createEruptionEvents(seed,15);
  // Three intersecting, warped sheets give each plume volume from every view.
  const positions = [], uvs = [], sheets = [], indices = [];
  for (let sheet=0;sheet<3;sheet++) {
    const base = positions.length/3;
    for (let i=0;i<=64;i++) for (let j=0;j<=16;j++) {
      positions.push(0,0,0); uvs.push(i/64,j/16); sheets.push(sheet*Math.PI/3);
      if(i<64 && j<16) { const k=base+i*17+j; indices.push(k,k+17,k+1,k+1,k+17,k+18); }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));
  geometry.setAttribute('sheet',new THREE.Float32BufferAttribute(sheets,1));
  geometry.setIndex(indices);
  const fragmentGeometry = new THREE.BufferGeometry();
  const fragmentSeeds = [];
  let fragmentSeed = seed >>> 0;
  for(let i=0;i<360*3;i++) {
    fragmentSeed = (1664525*fragmentSeed+1013904223)>>>0;
    fragmentSeeds.push(fragmentSeed/4294967296);
  }
  fragmentGeometry.setAttribute('position',new THREE.Float32BufferAttribute(new Float32Array(360*3),3));
  fragmentGeometry.setAttribute('seed',new THREE.Float32BufferAttribute(fragmentSeeds,3));
  const vertexShader = /* glsl */ `
    uniform float plumeLength, plumeWidth, span, bend, twist, age, growth, mode, eventSeed;
    attribute float sheet;
    varying vec2 vUv;
    varying float vSheet;
    void main() {
      vUv = uv; vSheet = sheet;
      float u = uv.x, across = uv.y*2.0-1.0;
      float angle = sheet + u*twist;
      float ripple = sin(u*19.0-age*9.0+eventSeed)*.12+sin(u*37.0+eventSeed)*.045;
      float width = plumeWidth*(.36+u*.9)*(1.0+ripple);
      vec3 p;
      if(mode < .5) {
        // A rapidly expanding, bending fan; its outer material is progressively wider.
        p = vec3(bend*u*u*growth, sin(u*3.0+eventSeed)*u*u*.12, .995+u*plumeLength*growth);
        p += vec3(cos(angle),sin(angle),0.0)*across*width;
        p.z += sin(across*5.0+u*22.0-age*6.0)*u*.018;
      } else {
        float a = u*3.14159265;
        p = vec3(cos(a)*span, bend*sin(a)*.22, sqrt(max(1.0-span*span,0.0))-.012+sin(a)*plumeLength*growth);
        vec3 outward = normalize(vec3(plumeLength*growth*cos(a),0.0,span*sin(a)));
        p += (vec3(0.0,1.0,0.0)*cos(angle)+outward*sin(angle))*across*plumeWidth*(.45+.55*sin(a));
        p.y += ripple*sin(a)*.08;
      }
      gl_Position = projectionMatrix*modelViewMatrix*vec4(p,1.0);
    }
  `;
  const fragmentShader = /* glsl */ `
    uniform float time, flareStrength, strength, power, age, mode, eventSeed;
    varying vec2 vUv;
    varying float vSheet;
    ${noise}
    void main() {
      vec2 uv = clamp(vUv,0.0,1.0);
      float u = uv.x, v = uv.y*2.0-1.0;
      float flow = time*.35;
      float billow = fbm(vec3(u*6.0-flow,v*3.5+eventSeed,vSheet+eventSeed));
      float edge = max(1.0-abs(v)-(billow-.45)*.65,0.0);
      float softEdge = smoothstep(0.0,.36,edge);
      float strands = noise3(vec3(u*18.0-flow*2.0,v*24.0+billow*4.0,eventSeed+vSheet));
      float veins = pow(clamp(strands,0.0,1.0),5.0);
      float ragged = smoothstep(.25,.65,billow+strands*.25);
      float tip = mode < .5 ? 1.0-smoothstep(.60,1.0,u+(billow-.5)*.19) : 1.0;
      float rootDistance = mode < .5 ? u : min(u,1.0-u);
      float root = exp(-rootDistance*17.0)*pow(max(1.0-abs(v),0.0),2.0);
      vec3 color = vec3(1.5,.065,.001)*ragged + vec3(5.0,.85,.013)*veins;
      color += vec3(7.0,3.4,.65)*root*(.45+strands);
      float density = softEdge*tip*(.3+billow*.9)*strength*power*flareStrength*.43;
      // All power bases are bounded: never reintroduce NaNs into the bloom chain.
      gl_FragColor = vec4(color*density,1.0);
    }
  `;
  const slots = schedule.events.map(() => {
    const uniforms = {
      ...shared, time: shared.flareTime, plumeLength: {value: 0}, plumeWidth: {value: 0}, span: {value: 0},
      bend: {value: 0}, twist: {value: 0}, eventSeed: {value: 0}, mode: {value: 0},
      age: {value: 0}, growth: {value: 0}, strength: {value: 0}, power: {value: 0},
    };
    const material = new THREE.ShaderMaterial({uniforms,vertexShader,fragmentShader,
      side: THREE.DoubleSide,forceSinglePass: true,transparent: true,
      blending: THREE.AdditiveBlending,depthWrite: false});
    const mesh = new THREE.Mesh(geometry,material);
    mesh.frustumCulled = false; // The vertex shader creates the actual bounds.
    const fragments = new THREE.Points(fragmentGeometry,new THREE.ShaderMaterial({
      uniforms,
      vertexShader: /* glsl */ `
        uniform float age, plumeLength, plumeWidth, bend, twist, mode, eventSeed, pixelRatio;
        attribute vec3 seed;
        varying float vLight;
        void main() {
          float flight = clamp((age-seed.x*.20)/.65,0.0,1.0);
          float distance = plumeLength*(.5+seed.y)*flight;
          float spread = plumeWidth*(.4+flight*2.0);
          float angle = seed.z*6.28318+twist*flight;
          vec3 p = vec3(bend*flight*flight,0.0,1.0+distance);
          p.xy += vec2(cos(angle),sin(angle))*spread*seed.x;
          p.y += sin(eventSeed+flight*4.0)*flight*.14;
          vLight = smoothstep(.0,.04,flight)*(1.0-smoothstep(.35,1.0,flight))*(1.0-step(.5,mode));
          gl_PointSize = (.8+seed.y*2.0)*(1.0-flight*.5)*pixelRatio;
          gl_Position = projectionMatrix*modelViewMatrix*vec4(p,1.0);
        }
      `,
      fragmentShader: /* glsl */ `
        uniform float strength, power, flareStrength;
        varying float vLight;
        void main() {
          float radius = length(gl_PointCoord-.5)*2.0;
          float light = (1.0-smoothstep(.0,1.0,radius))*vLight*strength*power*flareStrength;
          gl_FragColor = vec4(vec3(1.8,.14,.002)*light*.45,1.0);
        }
      `,
      transparent: true, blending: THREE.AdditiveBlending,depthWrite: false,
    }));
    fragments.frustumCulled = false;
    mesh.add(fragments);
    group.add(mesh);
    return {mesh,uniforms,id: -1};
  });
  const normal = new THREE.Vector3(), tangent = new THREE.Vector3(), side = new THREE.Vector3();
  const up = new THREE.Vector3(0,1,0), basis = new THREE.Matrix4();
  function update(time) {
    schedule.update(time).forEach((event,i) => {
      const slot = slots[i], u = slot.uniforms;
      if(slot.id !== event.id) {
        slot.id = event.id;
        normal.set(Math.cos(event.latitude)*Math.cos(event.longitude),Math.sin(event.latitude),Math.cos(event.latitude)*Math.sin(event.longitude));
        tangent.crossVectors(up,normal).normalize().applyAxisAngle(normal,event.roll);
        side.crossVectors(normal,tangent).normalize();
        slot.mesh.quaternion.setFromRotationMatrix(basis.makeBasis(tangent,side,normal));
        for(const [key,value] of Object.entries({plumeLength:event.length,plumeWidth:event.width,span:event.span,bend:event.bend,twist:event.twist,eventSeed:event.textureSeed,power:event.power,mode:event.kind==='jet'?0:1})) u[key].value=value;
      }
      const envelope = eruptionEnvelope(event,time);
      u.age.value=envelope.age; u.growth.value=envelope.growth;
      u.strength.value=envelope.strength*eruptionParticipation(shared.flareActivity.value,i);
      slot.mesh.visible = u.strength.value>0 && shared.flareStrength.value>0;
    });
  }
  update(0);
  return {group,update};
}
