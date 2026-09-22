"""Create mesh sources and port the project's GLSL math to Unreal Custom HLSL.
Run with normal Python. Geometry is exported as OBJ; rendering is entirely Unreal.
"""
from pathlib import Path
import math, json, random, re

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'References'/'ThreeJS'
S=ROOT/'Shaders'; A=ROOT/'Assets'
S.mkdir(exist_ok=True); A.mkdir(exist_ok=True)
source=(SOURCE/'sun.js').read_text(encoding='utf8')
noise=source.split('const noise = /* glsl */ `')[1].split('`;')[0]
def hlsl(code):
    for a,b in [('vec2','float2'),('vec3','float3'),('vec4','float4'),('fract','frac'),('mix','lerp')]:
        code=re.sub(r'\b'+a+r'\b',b,code)
    return code
common='struct SolarMath {\n'+hlsl(noise)+'''
float3 rx(float3 p,float a){float c=cos(a),s=sin(a);return float3(p.x,c*p.y-s*p.z,s*p.y+c*p.z);}
float3 ry(float3 p,float a){float c=cos(a),s=sin(a);return float3(c*p.x+s*p.z,p.y,-s*p.x+c*p.z);}
float3 rz(float3 p,float a){float c=cos(a),s=sin(a);return float3(c*p.x-s*p.y,s*p.x+c*p.y,p.z);}
float3 rotate(float3 p,float t){return rx(ry(rz(p,-.12),.4+t*.018),.15);}
float3 inverse(float3 p,float t){return rz(ry(rx(p,-.15),-.4-t*.018),.12);}
float3 toUE(float3 p){return float3(p.z,p.x,p.y)*100.;}
float3 fromUE(float3 p){return float3(p.y,p.z,p.x)/100.;}
float smooth(float x){x=saturate(x);return x*x*(3.-2.*x);}
'''

class RNG:
    def __init__(self,seed):self.state=seed
    def random(self):
        self.state=(1664525*self.state+1013904223)&0xffffffff
        return self.state/4294967296
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):
    length=math.sqrt(sum(x*x for x in a));return tuple(x/length for x in a)
def rotate_axis(p,n,a):
    c,s=math.cos(a),math.sin(a);k=cross(n,p);d=sum(x*y for x,y in zip(n,p))
    return tuple(p[i]*c+k[i]*s+n[i]*d*(1-c) for i in range(3))
def vec(a):return 'float3('+','.join(f'{x:.9f}' for x in a)+')'
rng=RNG(73491);loops=[]
for i in range(72):
    az=rng.random()*math.tau;lat=(rng.random()-.5)*2.2
    n=(math.cos(lat)*math.cos(az),math.sin(lat),math.cos(lat)*math.sin(az))
    tangent=rotate_axis(norm(cross(n,(0,1,0))),n,rng.random()*math.pi)
    loops.append(dict(normal=n,tangent=tangent,height=.10+rng.random()*.23,width=.10+rng.random()*.15,phase=rng.random()*math.tau,rate=.15+rng.random()*.16))
common+='void loopData(int id,out float3 n,out float3 tang,out float4 data){\n'
for i,l in enumerate(loops):
    common+=f'if(id=={i}){{n={vec(l["normal"])};tang={vec(l["tangent"])};data=float4({l["height"]},{l["width"]},{l["phase"]},{l["rate"]});return;}}\n'
common+='n=float3(0,1,0);tang=float3(1,0,0);data=0;}\n'

# Same LCG/event distributions as the web scene, precomputed for a finite shot.
rng=RNG(29173); serial=0
def create(start,slot):
    global serial
    violent=rng.random()<.26; duration=11+rng.random()*17; mode=1 if rng.random()<.4 else 0
    longitude=rng.random()*math.tau;latitude=(rng.random()-.5)*1.8;roll=rng.random()*math.tau
    e=dict(id=serial,slot=slot,start=start,duration=duration,violent=violent,mode=mode,longitude=longitude,latitude=latitude,roll=roll,
           length=(.65+rng.random()*.45) if violent else (.25+rng.random()*.35),width=(.15+rng.random()*.13) if violent else (.055+rng.random()*.085),
           span=.13+rng.random()*.23,bend=(rng.random()-.5)*.7,twist=(rng.random()-.5)*2.4,texture_seed=rng.random()*100,
           power=(1.2+rng.random()*.7) if violent else (.65+rng.random()*.5))
    serial+=1;return e
slots=[create(-4-i*3 if i<2 else 3+rng.random()*22,i) for i in range(15)]
events=list(slots)
for step in range(1,1201):
    t=step*.05
    for i,e in enumerate(slots):
        if t>=e['start']+e['duration']:
            slots[i]=create(e['start']+e['duration']+5+rng.random()*24,i);events.append(slots[i])
common+='void eventData(int id,out float4 a,out float4 b,out float4 c,out float3 n,out float3 tang){\n'
for i,e in enumerate(events):
    lat,lon=e['latitude'],e['longitude'];n=(math.cos(lat)*math.cos(lon),math.sin(lat),math.cos(lat)*math.sin(lon))
    tang=rotate_axis(norm(cross((0,1,0),n)),n,e['roll'])
    common+=f'if(id=={i}){{a=float4({e["start"]},{e["duration"]},{e["slot"]},{e["mode"]});b=float4({e["length"]},{e["width"]},{e["span"]},{e["bend"]});c=float4({e["twist"]},{e["texture_seed"]},{e["power"]},0);n={vec(n)};tang={vec(tang)};return;}}\n'
common+='a=float4(1000,10,15,0);b=0;c=0;n=float3(0,0,1);tang=float3(1,0,0);}\n};\nSolarMath solar;\n'
(S/'Common.hlsl').write_text(common)

surface=source.split('float t = time * .055;')[1].split('gl_FragColor = vec4(color, 1.0);')[0]
surface='float t = time * .055;'+surface
surface=surface.replace('max(normalize(vNormal).z, 0.0)','max(normalize(worldP).z, 0.0)')
surface=hlsl(surface)
surface=re.sub(r'\b(fbm|noise3)\(',r'solar.\1(',surface)
(S/'Surface.hlsl').write_text('float time=SolarTime*SurfaceFlow; float sunspots=Sunspots;\nfloat3 worldP=solar.fromUE(World);float3 p=normalize(solar.inverse(worldP,SolarTime*RotationSpeed));\n'+surface+'\nreturn float4(color,1);')
corona=source.split('vec2 p = (vUv - .5) * 4.8;')[1].split('gl_FragColor = vec4(color * strength * coronaStrength * .65,1.0);')[0]
corona=hlsl('vec2 p = (vUv - .5) * 4.8;'+corona).replace('vUv','UV')
corona=re.sub(r'\b(fbm|noise3)\(',r'solar.\1(',corona)
(S/'Corona.hlsl').write_text('float time=SolarTime;float coronaStrength=CoronaGlow;\n'+corona+'\nreturn float4(color*strength*coronaStrength*.65,1);')

(S/'LoopPosition.hlsl').write_text('''
int id=(int)floor(UV.x/2.);float u=UV.x-id*2.,v=UV.y*2.-1.;
float3 n,tang;float4 data;solar.loopData(id,n,tang,data);float3 side=cross(n,tang);
float t=SolarTime*FlareActivity;float phase=data.z;
float life=smoothstep(-.5,.7,.65*sin(t*data.w+phase)+.35*sin(t*data.w*1.713+phase*3.1));
life*=saturate(FlareActivity*24.-id);
float thick=.012+.026*pow(.5+.5*sin(phase*7.3),3.);
float3 p=n*(.985+sin(u*3.14159265)*data.x)+tang*cos(u*3.14159265)*data.y+side*v*thick;
float h=max(length(p)-1.,0.);p+=normalize(p)*h*(life-.5)*.32;
p+=normalize(p)*sin(u*24.-t*1.1+phase)*.004*sin(u*3.14159265);
return solar.toUE(solar.rotate(p,SolarTime*RotationSpeed))*SunSize-World;
''')
(S/'Loop.hlsl').write_text('''
int id=(int)floor(UV.x/2.);float u=UV.x-id*2.;float3 n,tang;float4 data;solar.loopData(id,n,tang,data);
float t=SolarTime*FlareActivity,phase=data.z;
float life=smoothstep(-.5,.7,.65*sin(t*data.w+phase)+.35*sin(t*data.w*1.713+phase*3.1))*saturate(FlareActivity*24.-id);
float profile=max(1.-abs(UV.y-.5)*2.,0.);float thread=pow(profile,2.5),core=pow(profile,12.);
float flow=.65+.35*sin(u*65.-t*3.+phase);
return float4(lerp(float3(2.,.10,.002),float3(3.8,1.1,.065),core)*life*thread*flow*FlareIntensity,1);
''')

eventsetup='''
int id=(int)floor(UV.x/8.);float rem=UV.x-id*8.;int sheet=(int)floor(rem/2.);
float u=rem-sheet*2.,v=UV.y*2.-1.;float4 a,b,c;float3 n,tang;solar.eventData(id,a,b,c,n,tang);
float time=SolarTime*FlareActivity,age=saturate((time-a.x)/a.y);
float strength=solar.smooth(age/.12)*(1.-solar.smooth((age-.48)/.52))*saturate(FlareActivity*5.-a.z);
float growth=.16+.84*(1.-pow(1.-age,3.));float mode=a.w,eventSeed=c.y;
'''
(S/'PlumePosition.hlsl').write_text(eventsetup+'''
float angle=sheet*3.14159265/3.+u*c.x;
float ripple=sin(u*19.-age*9.+eventSeed)*.12+sin(u*37.+eventSeed)*.045;
float width=b.y*(.36+u*.9)*(1.+ripple);float3 p;
if(mode<.5){
 p=float3(b.w*u*u*growth,sin(u*3.+eventSeed)*u*u*.12,.995+u*b.x*growth);
 p+=float3(cos(angle),sin(angle),0)*v*width;p.z+=sin(v*5.+u*22.-age*6.)*u*.018;
}else{
 float angleU=u*3.14159265;
 p=float3(cos(angleU)*b.z,b.w*sin(angleU)*.22,sqrt(max(1.-b.z*b.z,0.))-.012+sin(angleU)*b.x*growth);
 float3 outward=normalize(float3(b.x*growth*cos(angleU),0,b.z*sin(angleU)));
 p+=(float3(0,1,0)*cos(angle)+outward*sin(angle))*v*b.y*(.45+.55*sin(angleU));p.y+=ripple*sin(angleU)*.08;
}
p=tang*p.x+cross(n,tang)*p.y+n*p.z;
return solar.toUE(solar.rotate(p,SolarTime*RotationSpeed))*SunSize-World;
''')
eruption=(SOURCE/'eruptions.js').read_text(encoding='utf8')
frag=eruption.split('float flow = time*.35;')[1].split('// All power bases')[0]
frag=hlsl('float flow = time*.35;'+frag)
frag=re.sub(r'\b(fbm|noise3)\(',r'solar.\1(',frag)
(S/'Plume.hlsl').write_text(eventsetup+'float vSheet=sheet*3.14159265/3.;float power=c.z,flareStrength=FlareIntensity;\n'+frag+'\nreturn float4(color*density,1);')

(S/'Stars.hlsl').write_text('''
float r=length(UV-.5)*2.;float light=pow(max(1.-r,0.),2.);
return float4(float3(.75,.48,.25)*light*Stars,1);
''')

# OBJ UVs are flipped by the importer, so write 1-v to preserve the shader UVs.
def obj(name,verts,uvs,faces):
    with (A/(name+'.obj')).open('w') as f:
        f.write('o '+name+'\n')
        for v in verts:f.write('v '+' '.join(f'{x:.7f}' for x in v)+'\n')
        for u,v in uvs:f.write(f'vt {u:.7f} {1-v:.7f}\n')
        for face in faces:f.write('f '+' '.join(f'{i+1}/{i+1}' for i in face)+'\n')
def grids(name,count,rows,cols,stride,sheets=1):
    vertices=[];uv=[];faces=[]
    for idx in range(count):
        for sheet in range(sheets):
            base=len(vertices)
            for j in range(rows+1):
                for k in range(cols+1):
                    u=j/rows;v=k/cols
                    # Broad static bounds accommodate GPU-generated geometry.
                    # Distinct placeholder positions avoid quadratic overlapping-
                    # vertex work in the importer. WPO supplies final positions.
                    vertices.append(((idx*sheets+sheet)*.003,(u-.5)*400,(v-.5)*400))
                    uv.append((idx*stride+sheet*2+u,v))
                    if j<rows and k<cols:
                        q=base+j*(cols+1)+k;faces.append((q,q+cols+1,q+cols+2,q+1))
    obj(name,vertices,uv,faces)
grids('MagneticLoops',72,80,1,2)
grids('PlasmaEjections',len(events),64,16,8,3)
# Interchange preserves OBJ axes. Camera looks down -X, so these lie in YZ.
obj('CoronaPlane',[(0,-240,-240),(0,240,-240),(0,240,240),(0,-240,240)],[(0,0),(1,0),(1,1),(0,1)],[(0,1,2,3)])
r=random.Random(9182);verts=[];uv=[];faces=[]
for i in range(1800):
    x=r.uniform(-630,630);y=r.uniform(-360,360);size=.12+r.random()**5*.8
    base=len(verts);verts.extend([(0,x-size,y-size),(0,x+size,y-size),(0,x+size,y+size),(0,x-size,y+size)])
    uv.extend([(0,0),(1,0),(1,1),(0,1)]);faces.append((base,base+1,base+2,base+3))
obj('StarField',verts,uv,faces)

particle_setup='''
int id=(int)floor(UV.x/2.);float2 corner=float2(UV.x-id*2.,UV.y);
float3 seed=float3(solar.hash(float3(id,.71,2.31)),solar.hash(float3(id,1.17,5.1)),solar.hash(float3(id,3.19,7.3)));
float time=SolarTime*FlareActivity;float3 p;float light;float3 color;
if(id<5400){
 int loopId=id%72;float3 n,tang;float4 data;solar.loopData(loopId,n,tang,data);
 float life=frac(time*(.065+seed.y*.065)+seed.x);
 float eruption=smoothstep(.15,.90,sin(time*.23+floor(seed.x*9.)));
 float height=life*(.18+seed.z*.55);
 p=n*(1.005+height)+tang*((seed.y-.5)*.10+life*life*.22)+cross(n,tang)*(seed.z-.5)*life*.11;
 light=pow(1.-life,2.)*smoothstep(0.,.08,life)*eruption*saturate(FlareActivity*24.-loopId);
 color=float3(2.8,.58,.018);
}else{
 int eventId=(id-5400)/360;float4 a,b,c;float3 n,tang;solar.eventData(eventId,a,b,c,n,tang);
 float age=saturate((time-a.x)/a.y);float strength=solar.smooth(age/.12)*(1.-solar.smooth((age-.48)/.52))*saturate(FlareActivity*5.-a.z);
 float flight=saturate((age-seed.x*.20)/.65),distance=b.x*(.5+seed.y)*flight;
 float spread=b.y*(.4+flight*2.),angle=seed.z*6.28318+c.x*flight;
 float3 local=float3(b.w*flight*flight,0,1.+distance);
 local.xy+=float2(cos(angle),sin(angle))*spread*seed.x;local.y+=sin(c.y+flight*4.)*flight*.14;
 p=tang*local.x+cross(n,tang)*local.y+n*local.z;
 light=smoothstep(0.,.04,flight)*(1.-smoothstep(.35,1.,flight))*(1.-step(.5,a.w))*strength*c.z;
 color=float3(1.8,.14,.002)*.45;
}
'''
(S/'ParticlePosition.hlsl').write_text(particle_setup+'''
float3 pos=solar.toUE(solar.rotate(p,SolarTime*RotationSpeed))*SunSize;
pos.yz+=(corner-.5)*(.8+seed.z*1.1);
return pos-World;
''')
(S/'Particles.hlsl').write_text(particle_setup+'''
float r=length(corner-.5)*2.;float alpha=(1.-smoothstep(0.,1.,r))*light*FlareIntensity;
return float4(color*alpha,1);
''')
grids('EjectaParticles',5400+360*len(events),1,1,2)
(A/'events.json').write_text(json.dumps(events,indent=2))
(A/'loops.json').write_text(json.dumps(loops,indent=2))
print('Prepared HLSL and geometry:',len(loops),'loops,',len(events),'scheduled ejections')
