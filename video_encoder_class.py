import ffmpeg
import os
from typing import Dict

class VideoEncoder:
    # Supported formats with codec relationships
    SUPPORTED_CONTAINERS: Dict[str, Dict] = {
        'mp4': {
            'video': ['libx264', 'libx265', 'libaom-av1', 'mpeg4'],
            'audio': ['aac', 'mp3', 'flac'],
            'default_video': 'libx264',
            'default_audio': 'aac'
        },
        'mkv': {
            'video': ['libx264', 'libx265', 'libaom-av1', 'vp9', 'av1'],
            'audio': ['flac', 'aac', 'opus', 'vorbis'],
            'default_video': 'libx264',
            'default_audio': 'flac'
        },
        'webm': {
            'video': ['libvpx-vp9', 'libaom-av1'],
            'audio': ['libopus'],
            'default_video': 'libvpx-vp9',
            'default_audio': 'libopus'
        },
        'mov': {
            'video': ['libx264', 'libx265', 'prores_ks'],
            'audio': ['aac', 'alac'],
            'default_video': 'libx264',
            'default_audio': 'aac'
        },
        'avi': {'video': ['mpeg4', 'msmpeg4v3'], 'audio': ['mp3'], 'default_video': 'mpeg4', 'default_audio': 'mp3'},
        'flv': {'video': ['flv1'], 'audio': ['mp3'], 'default_video': 'flv1', 'default_audio': 'mp3'},
        # Add other containers as needed...
    }

    AUDIO_CODEC_MAP: Dict[str, str] = {
        'mp3': 'libmp3lame',
        'aac': 'aac',
        'flac': 'flac',
        'opus': 'libopus',
        'wav': 'pcm_s16le',
        'alac': 'alac',
        'vorbis': 'libvorbis',
        'ac3': 'ac3',
        'dts': 'dca'
    }

    def __init__(self, source: str):
        self.source = source
        self._video_codec = None
        self._audio_codec = None
        self.output_file = None
        self.video_filters = []
        self.audio_filters = []
        self.extra_args = {}

    def set_output(self, output_path: str, **kwargs):
        """
        Auto-configures codecs based on file extension and user overrides.
        """
        ext = os.path.splitext(output_path)[1].lower().lstrip('.')

        if ext not in self.SUPPORTED_CONTAINERS:
            raise ValueError(f"Unsupported container: {ext}. Choose from {list(self.SUPPORTED_CONTAINERS.keys())}")

        container = self.SUPPORTED_CONTAINERS[ext]

        # Set video codec
        vcodec = kwargs.get('vcodec', container['default_video'])
        if vcodec not in container['video']:
            raise ValueError(f"Video codec {vcodec} not supported in {ext}. Valid options: {container['video']}")
        self._video_codec = vcodec

        # Set audio codec with proper mapping
        acodec = kwargs.get('acodec', container['default_audio'])
        mapped_acodec = self.AUDIO_CODEC_MAP.get(acodec, acodec)
        if mapped_acodec not in container['audio']:
            raise ValueError(f"Audio codec {acodec} not supported in {ext}. Valid options: {container['audio']}")
        self._audio_codec = mapped_acodec

        self.output_file = output_path
        self.extra_args = {k: v for k, v in kwargs.items() if k not in ('vcodec', 'acodec')}

    def add_trim(self, start: float, end: float):
        """Add trim filter with PTS reset for accurate seeking"""
        self.video_filters.append(f'trim=start={start}:end={end},setpts=PTS-STARTPTS')
        self.audio_filters.append(f'atrim=start={start}:end={end},asetpts=PTS-STARTPTS')

    def encode(self, overwrite: bool = True):
        """Execute encoding with current configuration"""
        if not self.output_file:
            raise ValueError("Output path not configured. Call set_output() first.")

        input_stream = ffmpeg.input(self.source)

        # Build filter chains
        video = input_stream.video
        for vf in self.video_filters:
            video = video.filter_multi_output(vf)

        audio = input_stream.audio
        for af in self.audio_filters:
            audio = audio.filter_multi_output(af)

        args = {
            'c:v': self._video_codec,
            'c:a': self._audio_codec,
            **self.extra_args
        }

        if overwrite:
            args['y'] = None

        try:
            ffmpeg.output(video, audio, self.output_file, **args).run()
            print(f"Successfully encoded to {self.output_file}")
        except ffmpeg.Error as e:
            print(f"FFmpeg error: {e.stderr.decode()}")
            raise

    
    @classmethod
    def create_av1_flac(cls, input_path: str, output_path: str, start: float = None, end: float = None):
        """
        Specialized method for AV1/FLAC encoding with optional trimming.
        Auto-selects appropriate container (mkv/webm).
        """
        encoder = cls(input_path)
        encoder.set_output(output_path, vcodec='libaom-av1', acodec='flac')

        if start is not None and end is not None:
            encoder.add_trim(start, end)

        # AV1 encoding defaults
        encoder.extra_args.update({
            'crf': '30',
            'cpu-used': '4',
            'row-mt': '1',
            'tile-columns': '2'
        })

        encoder.encode()


    @classmethod
    def encode_as_mp4_mp3(cls, input_path: str, output_path: str, 
                        start: float = None, end: float = None):
        """
        Encodes input video as MP4 with H.264 video and AAC audio.
        Also outputs an MP3 audio-only file (same basename).
        Optionally trims video between start/end times (in seconds).
        
        Args:
            input_path: Source video path
            output_path: Output MP4 path (auto-appends .mp4 if missing)
            start: Optional start time in seconds for trimming
            end: Optional end time in seconds for trimming
        """
        # Ensure proper .mp4 extension
        base_path, original_ext = os.path.splitext(output_path)
        if original_ext.lower() != '.mp4':
            output_path = f"{base_path}.mp4"
            print(f"Adjusted output path to: {output_path}")

        # Video with AAC audio (standard for MP4)
        encoder = cls(input_path)
        encoder.set_output(output_path, vcodec='libx264', acodec='aac')
        if start is not None and end is not None:
            if end <= start:
                raise ValueError("End time must be greater than start time")
            encoder.add_trim(start, end)
        encoder.extra_args.update({
            'movflags': '+faststart',
            'preset': 'medium',
            'shortest': None
        })
        encoder.encode()

        # Also create an MP3 audio-only file if requested
        mp3_output = f"{base_path}.mp3"
        audio_encoder = cls(input_path)
        audio_encoder.set_output(mp3_output, vcodec='none', acodec='mp3')
        if start is not None and end is not None:
            audio_encoder.add_trim(start, end)
        audio_encoder.extra_args.update({
            'q:a': '2'
        })
        audio_encoder.encode()