float time=SolarTime;float coronaStrength=CoronaGlow;
float2 p = (UV - .5) * 4.8;
        float r = length(p);
        float2 direction = p / max(r,.001);
        float breath = 1.0 + .045 * sin(time*.48);
        float d = max(r-1.0,0.0);
        float3 field = float3(direction*8.0, d*3.0-time*.11);
        float stream = solar.fbm(field);
        float rays = pow(solar.noise3(float3(direction*42.0,d*1.8-time*.23)),3.0);
        float halo = exp(-d*7.0/breath)*.44 + exp(-d*2.8)*.055;
        float wisps = exp(-d*(8.0-stream*4.0)/breath) * (stream*.7+rays*.65);
        float edge = exp(-d*65.0) * .55;
        float strength = (halo + wisps + edge) * smoothstep(.96,1.005,r);
        strength *= 1.0-smoothstep(1.85,2.35,r);
        float3 color = lerp(float3(1.0,.12,.004),float3(1.8,.59,.025),exp(-d*12.0));
        
return float4(color*strength*coronaStrength*.65,1);