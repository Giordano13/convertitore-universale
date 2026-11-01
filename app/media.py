"""FFprobe information, trimming, remux, audio replacement and video filters."""
from pathlib import Path
import json
import subprocess
from conversion_progress import run_process, report
from runtime_paths import media_executable


def probe(source):
    result = subprocess.run([media_executable('ffprobe'),'-v','error','-show_format','-show_streams','-of','json',str(source)],
                            capture_output=True,text=True,errors='replace',timeout=20,
                            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:
        raise RuntimeError('FFprobe non riesce a leggere il file: ' + result.stderr[-500:])
    data=json.loads(result.stdout)
    data['duration']=float(data.get('format',{}).get('duration',0) or 0)
    return data


def trim_arguments(options, duration):
    start=float(options.get('start',0) or 0);end=float(options.get('end',0) or 0)
    if start < 0 or (end and end <= start) or (duration and start >= duration):
        raise ValueError('Intervallo non valido: la fine deve seguire l’inizio e l’inizio deve essere nel file.')
    actual=(min(end,duration) if end and duration else end or duration)-start
    args=['-ss',str(start)] if start else []
    if end:args+=['-t',str(end-start)]
    return args,max(0,actual)


def convert_media(source,target,fmt,options=None,audio_only=False):
    options=options or {}
    info=probe(source);trim,duration=trim_arguments(options,info['duration'])
    cmd=[media_executable('ffmpeg'),'-y','-i',str(source)]+trim
    if options.get('metadata','remove')=='remove':cmd+=['-map_metadata','-1','-map_chapters','-1']
    else:cmd+=['-map_metadata','0']
    if audio_only:
        cmd+=['-vn','-ar','48000' if fmt=='opus' else '44100']
        if fmt=='opus':cmd+=['-c:a','libopus']
        if fmt=='aiff':cmd+=['-c:a','pcm_s16be']
        if fmt in ('mp3','aac','ogg','m4a','opus'):cmd+=['-b:a',options.get('bitrate','192k')]
        speed=float(options.get('speed',1) or 1)
        if speed!=1:cmd+=['-af',f'atempo={speed}'];duration/=speed
    else:
        filters=[]
        if options.get('denoise'):filters.append('hqdn3d=3:2:3:2')
        if options.get('width') and options.get('height'):
            filters.append(f"scale={int(options['width'])}:{int(options['height'])}:force_original_aspect_ratio=decrease:force_divisible_by=2")
        if options.get('fps'):filters.append(f"fps={int(options['fps'])}")
        if fmt=='gif':
            cmd+=['-filter_complex',','.join(filters+['split[a][b];[a]palettegen[p];[b][p]paletteuse']),'-an','-loop','0']
        else:
            if filters:cmd+=['-vf',','.join(filters)]
            crf=str(round(35-max(1,min(100,int(options.get('quality',90))))*.2))
            if fmt=='webm':cmd+=['-c:v','libvpx-vp9','-crf',crf,'-b:v','0','-c:a','libopus']
            elif fmt=='avi':cmd+=['-c:v','mpeg4','-q:v','4','-c:a','libmp3lame']
            else:cmd+=['-c:v','libx264','-crf',crf,'-preset','medium','-pix_fmt','yuv420p','-c:a','aac']
            target_mb=float(options.get('target_mb',0) or 0)
            if target_mb:
                if not duration:raise ValueError('Durata ignota: non posso stimare il peso.')
                rate=int(target_mb*1024**2*8/duration)-192000
                if rate < 64000:raise ValueError('Peso richiesto troppo basso per durata e audio. Aumentalo.')
                # Average-bitrate target, not a hard upper size limit.
                if '-crf' in cmd:
                    at=cmd.index('-crf');del cmd[at:at+2]
                if '-b:v' in cmd:
                    at=cmd.index('-b:v');del cmd[at:at+2]
                cmd+=['-b:v',str(rate),'-b:a','192k']
    cmd.append(str(target))
    run_process(cmd,duration=duration,ffmpeg=True)


def remux(source,target,fmt,options=None):
    options=options or {};data=probe(source)
    cmd=[media_executable('ffmpeg'),'-y','-i',str(source),'-map','0:v?','-map','0:a?','-map','0:s?','-c','copy']
    if options.get('metadata','remove')=='remove':cmd+=['-map_metadata','-1']
    cmd.append(str(target))
    try:run_process(cmd,duration=data['duration'],ffmpeg=True)
    except RuntimeError as error:
        raise RuntimeError('Tracce incompatibili con il contenitore. Usa la conversione normale. '+str(error))


def replace_audio(video,audio,target,options=None):
    data=probe(video)
    cmd=[media_executable('ffmpeg'),'-y','-i',str(video),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-shortest']
    if (options or {}).get('metadata','remove')=='remove':cmd+=['-map_metadata','-1']
    run_process(cmd+[str(target)],duration=data['duration'],ffmpeg=True)
