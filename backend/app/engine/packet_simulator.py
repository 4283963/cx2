import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Tuple, Optional


@dataclass
class NetworkSimConfig:
    video_fps: int = 30
    audio_sample_rate: int = 48000
    packet_loss_rate: float = 0.05
    burst_loss_prob: float = 0.3
    burst_max_length: int = 5
    simulation_duration_sec: float = 10.0
    video_packet_size: int = 1200
    audio_packet_size: int = 200
    video_bitrate_bps: int = 2000000
    audio_bitrate_bps: int = 128000
    random_seed: Optional[int] = 42


@dataclass
class PacketTrace:
    timestamps: np.ndarray
    packet_ids: np.ndarray
    is_video: np.ndarray
    sizes: np.ndarray
    is_lost: np.ndarray
    is_recovered: np.ndarray = field(default_factory=lambda: np.array([]))

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame({
            'timestamp': self.timestamps,
            'packet_id': self.packet_ids,
            'is_video': self.is_video,
            'size_bytes': self.sizes,
            'is_lost': self.is_lost,
        })
        if len(self.is_recovered) > 0:
            df['is_recovered'] = self.is_recovered
        return df


class PacketLossSimulator:
    def __init__(self, config: NetworkSimConfig):
        self.config = config
        if config.random_seed is not None:
            np.random.seed(config.random_seed)

    def generate_video_packets(self) -> Tuple[np.ndarray, np.ndarray]:
        cfg = self.config
        num_frames = int(cfg.video_fps * cfg.simulation_duration_sec)
        frame_timestamps = np.arange(num_frames) / cfg.video_fps

        packets_per_frame = max(1, int(cfg.video_bitrate_bps / cfg.video_fps / 8 / cfg.video_packet_size))
        total_packets = num_frames * packets_per_frame

        timestamps = np.repeat(frame_timestamps, packets_per_frame)
        jitter = np.random.uniform(0, 1.0 / cfg.video_fps, total_packets)
        timestamps = np.sort(timestamps + jitter)

        sizes = np.full(total_packets, cfg.video_packet_size, dtype=np.int32)
        return timestamps, sizes

    def generate_audio_packets(self) -> Tuple[np.ndarray, np.ndarray]:
        cfg = self.config
        audio_frame_duration = 0.02
        audio_packets_per_sec = int(1.0 / audio_frame_duration)
        total_packets = int(audio_packets_per_sec * cfg.simulation_duration_sec)

        timestamps = np.arange(total_packets) * audio_frame_duration
        sizes = np.full(total_packets, cfg.audio_packet_size, dtype=np.int32)
        return timestamps, sizes

    def _apply_burst_loss(self, total_packets: int) -> np.ndarray:
        cfg = self.config
        is_lost = np.zeros(total_packets, dtype=bool)
        i = 0
        while i < total_packets:
            if np.random.random() < cfg.burst_loss_prob:
                burst_len = np.random.randint(1, cfg.burst_max_length + 1)
                end = min(i + burst_len, total_packets)
                is_lost[i:end] = True
                i = end
            else:
                if np.random.random() < cfg.packet_loss_rate:
                    is_lost[i] = True
                i += 1
        return is_lost

    def simulate(self) -> PacketTrace:
        v_ts, v_sizes = self.generate_video_packets()
        a_ts, a_sizes = self.generate_audio_packets()

        v_count = len(v_ts)
        a_count = len(a_ts)

        all_timestamps = np.concatenate([v_ts, a_ts])
        all_sizes = np.concatenate([v_sizes, a_sizes])
        is_video = np.concatenate([np.ones(v_count, dtype=bool), np.zeros(a_count, dtype=bool)])

        sort_idx = np.argsort(all_timestamps)
        all_timestamps = all_timestamps[sort_idx]
        all_sizes = all_sizes[sort_idx]
        is_video = is_video[sort_idx]

        total_packets = len(all_timestamps)
        packet_ids = np.arange(total_packets)

        is_lost = self._apply_burst_loss(total_packets)

        return PacketTrace(
            timestamps=all_timestamps,
            packet_ids=packet_ids,
            is_video=is_video,
            sizes=all_sizes,
            is_lost=is_lost,
        )
