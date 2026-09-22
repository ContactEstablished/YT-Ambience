float time=SolarTime*SurfaceFlow; float sunspots=Sunspots;
float3 worldP=solar.fromUE(World);float3 p=normalize(solar.inverse(worldP,SolarTime*RotationSpeed));
float t = time * .055;
        float3 warp = float3(solar.fbm(p*5.0+float3(t,0,0)), solar.fbm(p*5.0+float3(0,t,8)), solar.fbm(p*5.0+float3(6,0,-t)));
        float3 q = p * 11.0 + warp * 2.6;
        float turbulence = solar.fbm(q * 2.6 + float3(0,t*.7,-t*.3));
        float fine = solar.noise3(p * 185.0 + warp * 9.0 + t);
        float grain = solar.noise3(p * 390.0 + warp * 12.0);
        float filaments = 1.0 - abs(solar.noise3(q * 5.4 + warp * 3.0 + t) * 2.0 - 1.0);
        float heat = clamp((turbulence-.45)*1.35 + .53 + (fine-.5)*.38 + (grain-.5)*.12, 0.0, 1.0);
        float3 color = lerp(float3(.19,.004,.0003), float3(1.4,.115,.001), smoothstep(.24,.57,heat));
        color = lerp(color, float3(2.6,.64,.012), smoothstep(.51,.84,heat));
        color += float3(.45,.12,.002) * pow(filaments, 11.0) * (.5 + heat);

        // Broad magnetic regions slowly evolve; smaller noise breaks up their edges.
        float field = solar.fbm(p * 4.9 + warp * .65 + float3(t*.20,0,-t*.17));
        float irregular = field + (solar.noise3(p*43.0+warp*3.0)-.5)*.055;
        float amount = sunspots;
        float spot = smoothstep(.60-amount*.028, .69-amount*.024, irregular);
        float umbra = smoothstep(.66-amount*.028, .72-amount*.024, irregular);
        float spotStrength = min(sunspots,1.0);
        color *= 1.0 - spot * .77 * spotStrength;
        color = lerp(color, float3(.065,.005,.001), umbra * .83 * spotStrength);
        float activeRegion = smoothstep(.61,.76,solar.fbm(p*8.0-warp+float3(0,t*.2,0)));
        color += float3(2.0,.65,.025) * activeRegion * .55;
        // Limb darkening gives the emissive surface its spherical volume.
        float facing = max(normalize(worldP).z, 0.0);
        color *= .48 + .52 * pow(facing, .28);
        color *= 1.0 + .018 * sin(time * .48);
        
return float4(color,1);