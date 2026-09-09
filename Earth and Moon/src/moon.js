import * as THREE from 'three';

// Screen-space direction of the composition's far-to-near shadow gradient.
export const LUNAR_SHADOW_DIRECTION = { down: 0.62, right: 0.38 };

// A seamless, seeded height field: crater bowls, raised rims, and fine regolith.
// Generated locally so the foreground has close-up detail without remote assets.
export function createMoon() {
  const size = 2048;
  const heights = new Float32Array(size * size);
  const cavities = new Float32Array(size * size);
  let seed = 91827;
  const random = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296; };
  for (let i = 0; i < heights.length; i++) heights[i] = 0.5 + (random() - 0.5) * 0.018;

  // Periodic value noise at several scales avoids a smooth, plastic-looking base.
  for (const [cells, amplitude] of [[8, 0.075], [32, 0.035], [128, 0.018]]) {
    const grid = Float32Array.from({ length: cells * cells }, () => random() - 0.5);
    for (let y = 0; y < size; y++) {
      const gy = y / size * cells, iy = Math.floor(gy);
      const fy = gy - iy, ty = fy * fy * (3 - 2 * fy);
      for (let x = 0; x < size; x++) {
        const gx = x / size * cells, ix = Math.floor(gx);
        const fx = gx - ix, tx = fx * fx * (3 - 2 * fx);
        const a = grid[iy * cells + ix];
        const b = grid[iy * cells + (ix + 1) % cells];
        const c = grid[((iy + 1) % cells) * cells + ix];
        const d = grid[((iy + 1) % cells) * cells + (ix + 1) % cells];
        heights[y * size + x] += amplitude * THREE.MathUtils.lerp(THREE.MathUtils.lerp(a, b, tx), THREE.MathUtils.lerp(c, d, tx), ty);
      }
    }
  }

  // Overlapping impacts, with many more small craters than large ones.
  for (let crater = 0; crater < 2800; crater++) {
    const cx = random() * size, cy = random() * size;
    const radius = 2.5 + Math.pow(random(), 4) * 70;
    const depth = 0.025 + radius / 75 * 0.19;
    const extent = Math.ceil(radius * 1.4);
    const ellipticity = 0.88 + random() * 0.24;
    // Give about 28% of craters a little extra interior shading. Derive the
    // selection from the index so the terrain and speckle seeds stay untouched.
    const shadowVariation = ((crater + 1) * 0.61803398875) % 1;
    const extraShadow = shadowVariation > 0.72
      ? 0.025 + 0.035 * (shadowVariation - 0.72) / 0.28 : 0;
    for (let y = Math.floor(cy) - extent; y <= cy + extent; y++) {
      for (let x = Math.floor(cx) - extent; x <= cx + extent; x++) {
        const angle = Math.atan2(y - cy, (x - cx) * ellipticity);
        // Broken, weathered rims instead of identical smooth circular depressions.
        const rimVariation = 1 + 0.045 * Math.sin(angle * 5 + crater * 1.7)
          + 0.025 * Math.sin(angle * 11 + crater * 0.9);
        const distance = Math.hypot((x - cx) * ellipticity, y - cy) / (radius * rimVariation);
        if (distance > 1.35) continue;
        const bowl = distance < 1 ? -depth * Math.pow(1 - distance * distance, 1.1) : 0;
        const rim = depth * 0.36 * Math.exp(-Math.pow((distance - 0.98) / 0.085, 2))
          * (0.85 + 0.15 * Math.sin(angle * 8 + crater));
        const peak = radius > 43 ? depth * 0.20 * Math.exp(-distance * distance * 65) : 0;
        const index = ((y + size) % size) * size + (x + size) % size;
        heights[index] += bowl + rim + peak;
        const interior = Math.max(0, -bowl / depth);
        cavities[index] = Math.max(cavities[index], interior * 0.06 + interior * interior * extraShadow);
      }
    }
  }

  // Fine, periodic regolith detail. A separate seed preserves the crater layout.
  let detailSeed = 47211;
  const detailRandom = () => { detailSeed = (1664525 * detailSeed + 1013904223) >>> 0; return detailSeed / 4294967296; };
  const grain = new Float32Array(size * size);
  for (const [cells, amplitude] of [[128, 0.5], [512, 0.3], [1024, 0.2]]) {
    const grid = Float32Array.from({ length: cells * cells }, () => detailRandom() - 0.5);
    for (let y = 0; y < size; y++) {
      const gy = y / size * cells, iy = Math.floor(gy);
      const fy = gy - iy, ty = fy * fy * (3 - 2 * fy);
      for (let x = 0; x < size; x++) {
        const gx = x / size * cells, ix = Math.floor(gx);
        const fx = gx - ix, tx = fx * fx * (3 - 2 * fx);
        const a = grid[iy * cells + ix], b = grid[iy * cells + (ix + 1) % cells];
        const c = grid[((iy + 1) % cells) * cells + ix];
        const d = grid[((iy + 1) % cells) * cells + (ix + 1) % cells];
        grain[y * size + x] += amplitude * THREE.MathUtils.lerp(THREE.MathUtils.lerp(a, b, tx), THREE.MathUtils.lerp(c, d, tx), ty);
      }
    }
  }

  const relief = new Uint8Array(size * size * 4);
  const albedo = new Uint8Array(size * size * 4);
  for (let i = 0; i < heights.length; i++) {
    const h = THREE.MathUtils.clamp(heights[i] + grain[i] * 0.026, 0, 1);
    // Neutral gray regolith: relief shapes the light, rather than painting bowls dark.
    // Keep the midtone steady while reducing height-based and cavity darkening.
    const shade = Math.round(((108 + h * 35) * 0.92 + grain[i] * 28) * (1 - cavities[i]));
    // RGB retains relief; alpha carries crater depth for localized shadowing.
    relief.set([h * 255, h * 255, h * 255, Math.min(1, cavities[i] / 0.12) * 255], i * 4);
    albedo.set([shade, shade, shade, 255], i * 4);
  }
  // Sparse tiny mineral flecks, baked into albedo so they move with the ground.
  // Wrapped coordinates keep the texture seamless across every tile boundary.
  for (let speck = 0; speck < 14000; speck++) {
    const cx = random() * size, cy = random() * size;
    const radius = 0.7 + random() * 1.6;
    const darkness = 0.15 + random() * 0.20;
    for (let y = Math.floor(cy - radius); y <= cy + radius; y++) {
      for (let x = Math.floor(cx - radius); x <= cx + radius; x++) {
        const distance = Math.hypot(x - cx, y - cy) / radius;
        if (distance > 1) continue;
        const index = (((y + size) % size) * size + (x + size) % size) * 4;
        const shade = 1 - darkness * (1 - distance * distance);
        for (let channel = 0; channel < 3; channel++) albedo[index + channel] *= shade;
      }
    }
  }
  function map(data, color = false) {
    const result = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
    result.wrapS = result.wrapT = THREE.RepeatWrapping;
    result.repeat.set(10, 6);
    result.magFilter = THREE.LinearFilter;
    result.minFilter = THREE.LinearMipmapLinearFilter;
    result.generateMipmaps = true;
    if (color) result.colorSpace = THREE.SRGBColorSpace;
    result.needsUpdate = true;
    return result;
  }
  const heightMap = map(relief);
  const colorMap = map(albedo, true);
  const material = new THREE.MeshStandardMaterial({
    map: colorMap, bumpMap: heightMap, bumpScale: 6.0,
    displacementMap: heightMap, displacementScale: 0.22, displacementBias: -0.11,
    roughness: 1, metalness: 0,
  });
  // Relief flattens only at the limb, preserving a perfectly locked horizon.
  material.onBeforeCompile = shader => {
    shader.vertexShader = 'varying vec2 vLunarFrame;\n' + shader.vertexShader;
    shader.fragmentShader = 'varying vec2 vLunarFrame;\n' + shader.fragmentShader;
    shader.vertexShader = shader.vertexShader.replace('#include <project_vertex>', `
      #include <project_vertex>
      vLunarFrame = gl_Position.xy / gl_Position.w * 0.5 + 0.5;
    `);
    // An art-directed sunlight falloff fixed to the composition. The crater mask
    // rotates with the ground, so each crater travels naturally into the shade.
    // Apply in linear light, before tone mapping, only to the Moon's material.
    shader.fragmentShader = shader.fragmentShader.replace('#include <opaque_fragment>', `
      float shadeDistance = ${LUNAR_SHADOW_DIRECTION.down} * (1.0 - vLunarFrame.y)
        + ${LUNAR_SHADOW_DIRECTION.right} * vLunarFrame.x;
      float sunlightFalloff = smoothstep(0.36, 1.0, shadeDistance);
      float groundLight = mix(1.0, 0.025, pow(sunlightFalloff, 1.35));
      // Lift the far-side light, tapering to zero before the dark near side.
      // This preserves the existing lower-right illumination and crater shadows.
      float farSideLight = 1.0 + 1.9 * (1.0 - smoothstep(0.16, 0.70, sunlightFalloff));
      float craterDepth = texture2D(bumpMap, vBumpMapUv).a;
      float craterShade = 1.0 - 0.88 * smoothstep(0.2, 0.9, sunlightFalloff)
        * pow(craterDepth, 0.7);
      outgoingLight *= groundLight * craterShade * farSideLight;
      #include <opaque_fragment>
    `);
    shader.fragmentShader = shader.fragmentShader.replace('#include <normal_fragment_maps>',
      THREE.ShaderChunk.normal_fragment_maps.replace('dHdxy_fwd()',
        'dHdxy_fwd() * smoothstep(0.04, 0.3, abs(normal.z))'));
    shader.vertexShader = shader.vertexShader.replace('#include <displacementmap_vertex>', `
      vec3 worldNormal = normalize(mat3(modelMatrix) * objectNormal);
      float limbFade = smoothstep(0.15, 0.55, abs(worldNormal.z));
      transformed += normalize(objectNormal) *
        (texture2D(displacementMap, vDisplacementMapUv).x * displacementScale + displacementBias) * limbFade;
    `);
  };
  const geometry = new THREE.SphereGeometry(1, 384, 256);
  // Place the UV equator across the visible terrain, avoiding polar stretching.
  geometry.rotateX(Math.PI / 2);
  const moon = new THREE.Mesh(geometry, material);
  // Relief values are specified before the mesh is scaled to its foreground size.
  material.displacementScale = 0.0035;
  material.displacementBias = -0.00175;
  moon.rotation.set(0.22, 0.3, -0.15);
  return { moon, textures: [heightMap, colorMap] };
}
