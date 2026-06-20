import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Tuple, Optional, List


@dataclass
class BlockageEvent:
    event_id: int
    start_time_sec: float
    end_time_sec: float
    duration_sec: float
    description: str = "网络彻底阻断 - 隧道/电梯模式"


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
    network_profile: str = "NORMAL"
    blockage_window_count: int = 5
    blockage_window_ms: int = 500


@dataclass
class PacketTrace:
    timestamps: np.ndarray
    packet_ids: np.ndarray
    is_video: np.ndarray
    sizes: np.ndarray
    is_lost: np.ndarray
    is_recovered: Optional[np.ndarray] = None

    def has_recovery(self) -> bool:
        return self.is_recovered is not None and len(self.is_recovered) == len(self.is_lost)

    def get_recovered_safe(self) -> np.ndarray:
        if self.has_recovery():
            return self.is_recovered
        return np.zeros_like(self.is_lost, dtype=bool)

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame({
            'timestamp': self.timestamps,
            'packet_id': self.packet_ids,
            'is_video': self.is_video,
            'size_bytes': self.sizes,
            'is_lost': self.is_lost,
        })
        if self.has_recovery():
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

    def _generate_blockage_windows(self) -> List[BlockageEvent]:
        cfg = self.config
        events: List[BlockageEvent] = []
        if cfg.network_profile != "TUNNEL":
            return events

        total_dur = cfg.simulation_duration_sec
        win_dur = cfg.blockage_window_ms / 1000.0
        num_wins = cfg.blockage_window_count
        total_block_dur = win_dur * num_wins

        if total_block_dur >= total_dur * 0.8:
            start = 0.1 * total_dur
            for i in range(num_wins):
                s = start + i * win_dur
                e = min(s + win_dur, total_dur)
                events.append(BlockageEvent(
                    event_id=i + 1,
                    start_time_sec=float(s),
                    end_time_sec=float(e),
                    duration_sec=float(e - s),
                ))
            return events

        mid_point = total_dur * 0.45 + np.random.random() * (total_dur * 0.1)
        start_time = max(win_dur, mid_point - total_block_dur / 2.0)

        for i in range(num_wins):
            s = start_time + i * win_dur
            e = min(s + win_dur, total_dur)
            if s >= total_dur:
                break
            events.append(BlockageEvent(
                event_id=i + 1,
                start_time_sec=float(s),
                end_time_sec=float(e),
                duration_sec=float(e - s),
            ))
        return events

    def _apply_blockage_loss(
        self, timestamps: np.ndarray, is_lost: np.ndarray, events: List[BlockageEvent]
    ) -> np.ndarray:
        if not events:
            return is_lost
        forced = is_lost.copy()
        for ev in events:
            mask = (timestamps >= ev.start_time_sec) & (timestamps < ev.end_time_sec)
            forced[mask] = True
        return forced

    def simulate(self) -> Tuple[PacketTrace, List[BlockageEvent]]:
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
        blockage_events = self._generate_blockage_windows()
        is_lost = self._apply_blockage_loss(all_timestamps, is_lost, blockage_events)

        trace = PacketTrace(
            timestamps=all_timestamps,
            packet_ids=packet_ids,
            is_video=is_video,
            sizes=all_sizes,
            is_lost=is_lost,
        )
        return trace, blockage_events
