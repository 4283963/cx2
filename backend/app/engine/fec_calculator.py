import numpy as np
from dataclasses import dataclass
from typing import Tuple
from .packet_simulator import PacketTrace, NetworkSimConfig


@dataclass
class FECConfig:
    fec_type: str = "XOR"
    fec_ratio_k: int = 4
    fec_ratio_n: int = 5
    max_recovery_attempts: int = 2
    fec_overhead_bps: int = 0


class FECForwardErrorCorrection:
    def __init__(self, sim_config: NetworkSimConfig, fec_config: FECConfig):
        self.sim_config = sim_config
        self.fec_config = fec_config

    def _xor_recovery(self, is_lost: np.ndarray, group_size: int) -> np.ndarray:
        is_recovered = np.zeros_like(is_lost, dtype=bool)
        n = len(is_lost)
        for start in range(0, n, group_size):
            end = min(start + group_size, n)
            group = is_lost[start:end]
            lost_count = np.sum(group)
            if lost_count == 1 and len(group) >= self.fec_config.fec_ratio_k:
                lost_idx = np.where(group)[0][0]
                is_recovered[start + lost_idx] = True
        return is_recovered

    def _reed_solomon_recovery(self, is_lost: np.ndarray) -> np.ndarray:
        is_recovered = np.zeros_like(is_lost, dtype=bool)
        k = self.fec_config.fec_ratio_k
        n = self.fec_config.fec_ratio_n
        redundancy = n - k
        total = len(is_lost)

        for start in range(0, total, n):
            end = min(start + n, total)
            group = is_lost[start:end]
            lost_count = np.sum(group)
            if 0 < lost_count <= redundancy:
                lost_indices = np.where(group)[0]
                recoverable = min(lost_count, redundancy)
                for i in range(recoverable):
                    is_recovered[start + lost_indices[i]] = True
        return is_recovered

    def _interleaved_recovery(self, is_lost: np.ndarray, is_video: np.ndarray) -> np.ndarray:
        is_recovered = np.zeros_like(is_lost, dtype=bool)

        video_mask = is_video
        audio_mask = ~is_video

        v_lost = is_lost.copy()
        v_lost[audio_mask] = False
        is_recovered[video_mask] = self._reed_solomon_recovery(v_lost[video_mask])

        a_lost = is_lost.copy()
        a_lost[video_mask] = False
        is_recovered[audio_mask] = self._reed_solomon_recovery(a_lost[audio_mask])

        return is_recovered

    def apply_fec(self, trace: PacketTrace) -> Tuple[PacketTrace, FECConfig]:
        is_lost = trace.is_lost.copy()
        is_video = trace.is_video

        if self.fec_config.fec_type == "XOR":
            is_recovered = self._xor_recovery(is_lost, self.fec_config.fec_ratio_n)
        elif self.fec_config.fec_type == "RS":
            is_recovered = self._reed_solomon_recovery(is_lost)
        else:
            is_recovered = self._interleaved_recovery(is_lost, is_video)

        is_recovered = is_recovered & is_lost

        overhead_ratio = (self.fec_config.fec_ratio_n - self.fec_config.fec_ratio_k) / self.fec_config.fec_ratio_k
        v_bitrate = self.sim_config.video_bitrate_bps
        a_bitrate = self.sim_config.audio_bitrate_bps
        self.fec_config.fec_overhead_bps = int((v_bitrate + a_bitrate) * overhead_ratio)

        recovered_trace = PacketTrace(
            timestamps=trace.timestamps,
            packet_ids=trace.packet_ids,
            is_video=trace.is_video,
            sizes=trace.sizes,
            is_lost=trace.is_lost,
            is_recovered=is_recovered,
        )
        return recovered_trace, self.fec_config

    def calculate_effective_loss_rate(self, trace: PacketTrace) -> dict:
        total_lost = np.sum(trace.is_lost)
        total_packets = len(trace.is_lost)
        total_recovered = np.sum(trace.is_recovered) if len(trace.is_recovered) > 0 else 0
        remaining_lost = total_lost - total_recovered

        v_mask = trace.is_video
        a_mask = ~v_mask

        video_lost = np.sum(trace.is_lost[v_mask])
        video_recovered = np.sum(trace.is_recovered[v_mask]) if len(trace.is_recovered) > 0 else 0
        audio_lost = np.sum(trace.is_lost[a_mask])
        audio_recovered = np.sum(trace.is_recovered[a_mask]) if len(trace.is_recovered) > 0 else 0

        return {
            "total_packets": int(total_packets),
            "total_lost": int(total_lost),
            "total_recovered": int(total_recovered),
            "remaining_lost": int(remaining_lost),
            "raw_loss_rate": float(total_lost / total_packets) if total_packets > 0 else 0,
            "effective_loss_rate": float(remaining_lost / total_packets) if total_packets > 0 else 0,
            "recovery_rate": float(total_recovered / total_lost) if total_lost > 0 else 0,
            "video": {
                "lost": int(video_lost),
                "recovered": int(video_recovered),
                "recovery_rate": float(video_recovered / video_lost) if video_lost > 0 else 0,
            },
            "audio": {
                "lost": int(audio_lost),
                "recovered": int(audio_recovered),
                "recovery_rate": float(audio_recovered / audio_lost) if audio_lost > 0 else 0,
            },
        }
