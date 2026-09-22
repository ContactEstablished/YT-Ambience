import * as THREE from 'three';
import { createEruptions } from './eruptions.js';

// Object-space, seamless 3D noise: detail follows the rotating sphere, not the screen.
const noise = /* glsl */ `
  float hash(vec3 p) {
    p = fract(p * .3183099 + vec3(.11, .27, .43));
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
  }
  float noise3(vec3 p) {
    vec3 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(hash(i), hash(i+vec3(1,0,0)),f.x),
                   mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
               mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),
                   mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);
  }
  float fbm(vec3 p) {
    float sum = 0.0, amplitude = .5;
    for (int i = 0; i < 5; i++) {
      sum += amplitude * noise3(p);
      p = p * 2.03 + vec3(7.1, 3.7, 1.3);
      amplitude *= .5;
    }
    return sum;
  }
`;

export function createSun({ eruptionSeed = Math.floor(Math.random()*4294967296) } = {}) {
  const group = new THREE.Group();
  const uniforms = {
    time: { value: 0 }, flareTime: { value: 0 }, coronaTime: { value: 0 },
    sunspots: { value: 1 }, flareActivity: { value: 1 }, flareStrength: { value: 1 },
    coronaStrength: { value: 1 }, pixelRatio: { value: 1 },
  };
  const surface = new THREE.Mesh(new THREE.SphereGeometry(1, 128, 96), new THREE.ShaderMaterial({
    uniforms,
    vertexShader: /* glsl */ `
      varying vec3 vPosition;
      varying vec3 vNormal;
      void main() {
        vPosition = position;
        vNormal = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: /* glsl */ `
      uniform float time;
      uniform float sunspots;
      varying vec3 vPosition;
      varying vec3 vNormal;
      ${noise}
      void main() {
        vec3 p = normalize(vPosition);
        float t = time * .055;
        vec3 warp = vec3(fbm(p*5.0+vec3(t,0,0)), fbm(p*5.0+vec3(0,t,8)), fbm(p*5.0+vec3(6,0,-t)));
        vec3 q = p * 11.0 + warp * 2.6;
        float turbulence = fbm(q * 2.6 + vec3(0,t*.7,-t*.3));
        float fine = noise3(p * 185.0 + warp * 9.0 + t);
        float grain = noise3(p * 390.0 + warp * 12.0);
        float filaments = 1.0 - abs(noise3(q * 5.4 + warp * 3.0 + t) * 2.0 - 1.0);
        float heat = clamp((turbulence-.45)*1.35 + .53 + (fine-.5)*.38 + (grain-.5)*.12, 0.0, 1.0);
        vec3 color = mix(vec3(.19,.004,.0003), vec3(1.4,.115,.001), smoothstep(.24,.57,heat));
        color = mix(color, vec3(2.6,.64,.012), smoothstep(.51,.84,heat));
        color += vec3(.45,.12,.002) * pow(filaments, 11.0) * (.5 + heat);

        // Broad magnetic regions slowly evolve; smaller noise breaks up their edges.
        float field = fbm(p * 4.9 + warp * .65 + vec3(t*.20,0,-t*.17));
        float irregular = field + (noise3(p*43.0+warp*3.0)-.5)*.055;
        float amount = sunspots;
        float spot = smoothstep(.60-amount*.028, .69-amount*.024, irregular);
        float umbra = smoothstep(.66-amount*.028, .72-amount*.024, irregular);
        float spotStrength = min(sunspots,1.0);
        color *= 1.0 - spot * .77 * spotStrength;
        color = mix(color, vec3(.065,.005,.001), umbra * .83 * spotStrength);
        float activeRegion = smoothstep(.61,.76,fbm(p*8.0-warp+vec3(0,t*.2,0)));
        color += vec3(2.0,.65,.025) * activeRegion * .55;
        // Limb darkening gives the emissive surface its spherical volume.
        float facing = max(normalize(vNormal).z, 0.0);
        color *= .48 + .52 * pow(facing, .28);
        color *= 1.0 + .018 * sin(time * .48);
        gl_FragColor = vec4(color, 1.0);
      }
    `,
  }));
  group.add(surface);

  // This halo faces the fixed camera and sits behind the opaque sphere.
  const corona = new THREE.Mesh(new THREE.PlaneGeometry(4.8, 4.8), new THREE.ShaderMaterial({
    uniforms: { ...uniforms, time: uniforms.coronaTime },
    vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: /* glsl */ `
      uniform float time;
      uniform float coronaStrength;
      varying vec2 vUv;
      ${noise}
      void main() {
        vec2 p = (vUv - .5) * 4.8;
        float r = length(p);
        vec2 direction = p / max(r,.001);
        float breath = 1.0 + .045 * sin(time*.48);
        float d = max(r-1.0,0.0);
        vec3 field = vec3(direction*8.0, d*3.0-time*.11);
        float stream = fbm(field);
        float rays = pow(noise3(vec3(direction*42.0,d*1.8-time*.23)),3.0);
        float halo = exp(-d*7.0/breath)*.44 + exp(-d*2.8)*.055;
        float wisps = exp(-d*(8.0-stream*4.0)/breath) * (stream*.7+rays*.65);
        float edge = exp(-d*65.0) * .55;
        float strength = (halo + wisps + edge) * smoothstep(.96,1.005,r);
        strength *= 1.0-smoothstep(1.85,2.35,r);
        vec3 color = mix(vec3(1.0,.12,.004),vec3(1.8,.59,.025),exp(-d*12.0));
        gl_FragColor = vec4(color * strength * coronaStrength * .65,1.0);
      }
    `,
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false,
  }));
  corona.position.z = -1.15;

  // Magnetic arches are real 3D ribbons attached to surface positions. The sphere
  // occludes their far sides, and rotation carries them naturally over the limb.
  let seed = 73491;
  const random = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296; };
  const anchors = [];
  for (let i = 0; i < 72; i++) {
    const azimuth = random() * Math.PI * 2;
    const latitude = (random()-.5)*2.2;
    const normal = new THREE.Vector3(Math.cos(latitude)*Math.cos(azimuth), Math.sin(latitude), Math.cos(latitude)*Math.sin(azimuth));
    const tangent = new THREE.Vector3().crossVectors(normal, new THREE.Vector3(0,1,0)).normalize();
    tangent.applyAxisAngle(normal, random()*Math.PI);
    anchors.push({ normal, tangent, height: .10+random()*.23, width: .10+random()*.15, phase: random()*Math.PI*2, rate: .15+random()*.16 });
  }
  const positions = [], uvs = [], phases = [], rates = [], loopIndices = [], indices = [];
  for (const [loopIndex,anchor] of anchors.entries()) {
    const base = positions.length / 3;
    const side = new THREE.Vector3().crossVectors(anchor.normal,anchor.tangent).normalize();
    for (let j = 0; j <= 80; j++) {
      const u = j/80, angle = u*Math.PI;
      const point = anchor.normal.clone().multiplyScalar(.985 + Math.sin(angle)*anchor.height)
        .addScaledVector(anchor.tangent,Math.cos(angle)*anchor.width);
      for (const v of [-1,1]) {
        const thickness = .012 + .026 * (.5+.5*Math.sin(anchor.phase*7.3))**3;
        positions.push(...point.clone().addScaledVector(side,v*thickness).toArray());
        uvs.push(u,(v+1)/2); phases.push(anchor.phase); rates.push(anchor.rate);
        loopIndices.push(loopIndex);
      }
      if (j < 80) { const k = base+j*2; indices.push(k,k+1,k+2,k+1,k+3,k+2); }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));
  geometry.setAttribute('phase',new THREE.Float32BufferAttribute(phases,1));
  geometry.setAttribute('rate',new THREE.Float32BufferAttribute(rates,1));
  geometry.setAttribute('loopIndex',new THREE.Float32BufferAttribute(loopIndices,1));
  geometry.setIndex(indices);
  const arches = new THREE.Mesh(geometry,new THREE.ShaderMaterial({
    uniforms: { ...uniforms, time: uniforms.flareTime },
    vertexShader: /* glsl */ `
      uniform float time; uniform float flareActivity;
      attribute float phase; attribute float rate;
      attribute float loopIndex;
      varying vec2 vUv; varying float vLife; varying float vPhase;
      void main() {
        vUv = uv; vPhase = phase;
        vLife = smoothstep(-.5,.7,.65*sin(time*rate+phase)+.35*sin(time*rate*1.713+phase*3.1));
        vLife *= clamp(flareActivity*24.0-loopIndex,0.0,1.0);
        vec3 p = position;
        float height = max(length(p)-1.0,0.0);
        p += normalize(p) * height * ((vLife-.5)*.32);
        p += normalize(p)*sin(uv.x*24.0-time*1.1+phase)*.004*sin(uv.x*3.14159);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p,1.0);
      }
    `,
    fragmentShader: /* glsl */ `
      uniform float time; uniform float flareStrength;
      varying vec2 vUv; varying float vLife; varying float vPhase;
      void main() {
        float edge = abs(vUv.y-.5)*2.0;
        // Interpolation can overshoot the ribbon edge by a rounding error.
        // A fractional power of that negative value produces NaN, which bloom
        // spreads from one flare pixel across the frame. Clamp before pow().
        float profile = max(1.0-edge,0.0);
        float thread = pow(profile,2.5);
        float flow = .65+.35*sin(vUv.x*65.0-time*3.0+vPhase);
        float core = pow(profile,12.0);
        float strength = vLife * thread * flow * flareStrength;
        vec3 color = mix(vec3(2.0,.10,.002),vec3(3.8,1.1,.065),core);
        gl_FragColor = vec4(color*strength,1.0);
      }
    `,
    side: THREE.DoubleSide, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false,
  }));
  group.add(arches);

  const particlePositions = [], normals = [], tangents = [], seeds = [], particleLoops = [];
  for (let i = 0; i < 5400; i++) {
    const anchor = anchors[i % anchors.length];
    particlePositions.push(0,0,0);
    normals.push(...anchor.normal.toArray()); tangents.push(...anchor.tangent.toArray());
    seeds.push(random(),random(),random());
    particleLoops.push(i % anchors.length);
  }
  const particlesGeometry = new THREE.BufferGeometry();
  for (const [name,data] of [['position',particlePositions],['anchor',normals],['tangent',tangents],['seed',seeds]]) {
    particlesGeometry.setAttribute(name,new THREE.Float32BufferAttribute(data,3));
  }
  particlesGeometry.setAttribute('loopIndex',new THREE.Float32BufferAttribute(particleLoops,1));
  const particles = new THREE.Points(particlesGeometry,new THREE.ShaderMaterial({
    uniforms: { ...uniforms, time: uniforms.flareTime },
    vertexShader: /* glsl */ `
      uniform float time; uniform float flareActivity; uniform float pixelRatio;
      attribute float loopIndex;
      attribute vec3 anchor; attribute vec3 tangent; attribute vec3 seed;
      varying float vLight;
      void main() {
        float life = fract(time*(.065+seed.y*.065)+seed.x);
        float eruption = smoothstep(.15,.90,sin(time*.23+floor(seed.x*9.0)));
        float height = life*(.18+seed.z*.55);
        vec3 side = cross(anchor,tangent);
        vec3 p = anchor*(1.005+height) + tangent*((seed.y-.5)*.10 + life*life*.22)
               + side*(seed.z-.5)*life*.11;
        vLight = pow(1.0-life,2.0)*smoothstep(0.0,.08,life)*eruption;
        vLight *= clamp(flareActivity*24.0-loopIndex,0.0,1.0);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p,1.0);
        gl_PointSize = (1.0+seed.z*2.0)*pixelRatio;
      }
    `,
    fragmentShader: /* glsl */ `
      uniform float flareStrength;
      varying float vLight;
      void main() {
        float r = length(gl_PointCoord-.5)*2.0;
        float alpha = (1.0-smoothstep(.0,1.0,r))*vLight*flareStrength;
        gl_FragColor = vec4(vec3(2.8,.58,.018)*alpha,1.0);
      }
    `,
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false,
  }));
  particles.frustumCulled = false; // Positions are expanded on the GPU.
  group.add(particles);
  const eruptions = createEruptions(uniforms,noise,eruptionSeed);
  group.add(eruptions.group);
  return { group, corona, uniforms, update: () => eruptions.update(uniforms.flareTime.value) };
}
