import subprocess


def convert_video(input_path, output_path, out_format, width=None, height=None, fps=None, quality=90):
    fmt = out_format.lower()
    crf = str(round(35 - max(1, min(100, int(quality))) * .2))
    cmd = ['ffmpeg', '-y', '-i', input_path]
    filters = []
    if width and height:
        filters.append(f'scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2')
    if fps:
        filters.append(f'fps={fps}')
    if fmt == 'gif':
        chain = ','.join(filters + ['split[a][b];[a]palettegen[p];[b][p]paletteuse'])
        cmd += ['-filter_complex', chain, '-an', '-loop', '0']
    else:
        if filters:
            cmd += ['-vf', ','.join(filters)]
        if fmt == 'webm':
            cmd += ['-c:v', 'libvpx-vp9', '-crf', crf, '-b:v', '0', '-c:a', 'libopus']
        elif fmt == 'avi':
            cmd += ['-c:v', 'mpeg4', '-q:v', '4', '-c:a', 'libmp3lame']
        else:
            cmd += ['-c:v', 'libx264', '-crf', crf, '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac']
    cmd.append(output_path)
    result = subprocess.run(cmd, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('FFmpeg: ' + result.stderr[-1000:])
    return output_path
