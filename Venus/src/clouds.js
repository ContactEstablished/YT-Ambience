import * as THREE from 'three';

// Artistic cloud map inspired by the user's reference, not NASA observation data.
export async function applyCloudAppearance(model, renderer) {
  const clouds = await new THREE.TextureLoader().loadAsync(
    `${import.meta.env.BASE_URL}textures/venus-clouds-reference.png`,
  );
  clouds.colorSpace = THREE.SRGBColorSpace;
  clouds.flipY = false; // Match the NASA glTF sphere's UV convention.
  clouds.wrapS = THREE.RepeatWrapping;
  clouds.anisotropy = renderer.capabilities.getMaxAnisotropy();

  model.traverse(object => {
    if (!object.isMesh) return;
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    for (const material of materials) {
      material.map = clouds;
      material.roughness = 1;
      material.metalness = 0;
      material.onBeforeCompile = shader => {
        // Blend only a small band across the wrap to remove an image-edge seam.
        // Fade the very tip of each pole to a constant color to avoid UV pinching.
        shader.fragmentShader = shader.fragmentShader.replace(
          '#include <map_fragment>',
          `#ifdef USE_MAP
            vec2 cloudUv = vMapUv;
            vec4 cloudColor = texture2D(map, cloudUv);
            float edgeDistance = min(cloudUv.x, 1.0 - cloudUv.x);
            float seamBlend = 1.0 - smoothstep(0.0, 0.035, edgeDistance);
            vec4 otherEdge = texture2D(map, vec2(1.0 - cloudUv.x, cloudUv.y));
            cloudColor = mix(cloudColor, (cloudColor + otherEdge) * 0.5, seamBlend);
            float polarBlend = 1.0 - smoothstep(0.0, 0.035, min(cloudUv.y, 1.0 - cloudUv.y));
            cloudColor.rgb = mix(cloudColor.rgb, vec3(0.39, 0.48, 0.57), polarBlend);
            diffuseColor *= cloudColor;
          #endif`,
        );
      };
      material.customProgramCacheKey = () => 'venus-reference-clouds-v1';
      material.needsUpdate = true;
    }
  });
}
