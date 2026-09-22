"""Verify the final MP4 and PNG sequence using FFmpeg/Pillow."""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image,ImageStat
root=Path(__file__).resolve().parents[1]
files=sorted((root/'Renders'/'Frames').glob('Sun_*.png'))
assert [p.name for p in files]==[f'Sun_{i:04d}.png' for i in range(360)],'Missing/unexpected source frames'
means=[];hashes=set()
for path in files:
    with Image.open(path) as im:
        assert im.size==(1920,1080)
        means.append(sum(ImageStat.Stat(im.convert('RGB')).mean)/3)
    hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
assert len(hashes)==360, 'Duplicate source frames'
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries',
    'stream=codec_name,width,height,r_frame_rate,nb_frames:format=duration,size','-of','json',str(root/'Renders'/'Sun-Unreal.mp4')]))
stream=info['streams'][0]
assert stream['width']==1920 and stream['height']==1080 and stream['nb_frames']=='360' and stream['r_frame_rate']=='30/1'
subprocess.run(['ffmpeg','-v','error','-i',str(root/'Renders'/'Sun-Unreal.mp4'),'-f','null','-'],check=True)
delta=max(abs(b-a)/max(a,1e-6) for a,b in zip(means,means[1:]))*100
report={'passed':True,'video':info,'source_frames':len(files),'unique_frames':len(hashes),
        'minimum_global_mean_rgb':min(means),'maximum_global_mean_rgb':max(means),
        'largest_adjacent_global_brightness_change_percent':delta,
        'note':'Global brightness and frame continuity are checked; this does not prove absence of local aliasing or shimmer.'}
(root/'Renders'/'output_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
