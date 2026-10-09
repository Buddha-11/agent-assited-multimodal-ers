from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
from ..config import settings

class MediaError(Exception): pass

def ffmpeg_binary():
    if settings.ffmpeg_path:
        configured = shutil.which(settings.ffmpeg_path)
        if configured: return configured
        if Path(settings.ffmpeg_path).is_file(): return settings.ffmpeg_path
        raise MediaError('Configured FFmpeg binary was not found')
    binary = shutil.which('ffmpeg')
    if binary: return binary
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def command(args, timeout=90):
    try:
        result = subprocess.run([ffmpeg_binary(), '-nostdin', '-hide_banner', *args],
                                capture_output=True, timeout=timeout, shell=False)
        return result
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaError('Media processing unavailable or timed out') from exc

@dataclass
class ProcessedMedia:
    wav: Path | None
    frames: list[Path]
    duration: float

def process_media(source: Path, destination: Path) -> ProcessedMedia:
    # Browser WebM may omit duration metadata. Decode a bounded interval to validate
    # streams and measure the actual end timestamp without buffering the file.
    check = command(['-i', str(source), '-t', str(settings.max_recording_seconds + 1),
                     '-progress', 'pipe:1', '-f', 'null', '-'])
    stderr = check.stderr.decode(errors='replace')
    if check.returncode: raise MediaError('Invalid or unsupported media recording')
    times = re.findall(r'out_time_us=(\d+)', check.stdout.decode(errors='replace'))
    duration = max((int(t) / 1e6 for t in times), default=0)
    if duration <= 0.1: raise MediaError('Recording is empty or too short')
    if duration > settings.max_recording_seconds + 0.15: raise MediaError('Recording exceeds maximum duration')
    has_audio, has_video = 'Audio:' in stderr, 'Video:' in stderr
    if not has_audio and not has_video: raise MediaError('Recording contains no audio or video stream')
    wav = destination / 'audio.wav' if has_audio else None
    if wav:
        result = command(['-y', '-i', str(source), '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(wav)])
        if result.returncode: raise MediaError('Could not extract audio')
    if has_video:
        result = command(['-y', '-i', str(source), '-an', '-vf', f'fps=1/{settings.face_frame_interval},scale=640:-2',
                          '-frames:v', str(int(settings.max_recording_seconds / settings.face_frame_interval) + 1),
                          str(destination / 'frame-%03d.jpg')])
        if result.returncode: raise MediaError('Could not extract video frames')
    return ProcessedMedia(wav, sorted(destination.glob('frame-*.jpg')), duration)
