"""
Conversione audio: cambia formato, bitrate, sample rate, velocità.
Usa FFmpeg tramite subprocess (deve essere installato sul sistema).
"""
import subprocess


def convert_audio(input_path, output_path, out_format, bitrate="192k", sample_rate=44100, speed=1.0):
    """
    Converte un file audio in un altro formato.

    input_path: percorso del file originale
    output_path: dove salvare il file convertito
    out_format: 'mp3', 'wav', 'ogg', 'flac', 'aac'
    bitrate: es. '128k', '192k', '320k'
    sample_rate: es. 44100, 48000
    speed: moltiplicatore velocità (1.0 = normale, 1.5 = più veloce, 0.8 = più lento)
    """
    cmd = ["ffmpeg", "-y", "-i", input_path, "-vn", "-ar", str(sample_rate)]

    if out_format.lower() in ("mp3", "aac", "ogg", "m4a"):
        cmd += ["-b:a", bitrate]

    if speed != 1.0:
        cmd += ["-filter:a", f"atempo={speed}"]

    cmd.append(output_path)

    result = subprocess.run(cmd, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg ha fallito: {result.stderr[-500:]}")

    return output_path
