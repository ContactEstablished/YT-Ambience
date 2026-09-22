
int id=(int)floor(UV.x/8.);float rem=UV.x-id*8.;int sheet=(int)floor(rem/2.);
float u=rem-sheet*2.,v=UV.y*2.-1.;float4 a,b,c;float3 n,tang;solar.eventData(id,a,b,c,n,tang);
float time=SolarTime*FlareActivity,age=saturate((time-a.x)/a.y);
float strength=solar.smooth(age/.12)*(1.-solar.smooth((age-.48)/.52))*saturate(FlareActivity*5.-a.z);
float growth=.16+.84*(1.-pow(1.-age,3.));float mode=a.w,eventSeed=c.y;
float vSheet=sheet*3.14159265/3.;float power=c.z,flareStrength=FlareIntensity;
float flow = time*.35;
      float billow = solar.fbm(float3(u*6.0-flow,v*3.5+eventSeed,vSheet+eventSeed));
      float edge = max(1.0-abs(v)-(billow-.45)*.65,0.0);
      float softEdge = smoothstep(0.0,.36,edge);
      float strands = solar.noise3(float3(u*18.0-flow*2.0,v*24.0+billow*4.0,eventSeed+vSheet));
      float veins = pow(clamp(strands,0.0,1.0),5.0);
      float ragged = smoothstep(.25,.65,billow+strands*.25);
      float tip = mode < .5 ? 1.0-smoothstep(.60,1.0,u+(billow-.5)*.19) : 1.0;
      float rootDistance = mode < .5 ? u : min(u,1.0-u);
      float root = exp(-rootDistance*17.0)*pow(max(1.0-abs(v),0.0),2.0);
      float3 color = float3(1.5,.065,.001)*ragged + float3(5.0,.85,.013)*veins;
      color += float3(7.0,3.4,.65)*root*(.45+strands);
      float density = softEdge*tip*(.3+billow*.9)*strength*power*flareStrength*.43;
      
return float4(color*density,1);