import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List
from .packet_simulator import PacketTrace, NetworkSimConfig
from .fec_calculator import FECConfig


@dataclass
class QoSMetrics:
    video_recovery_rate: float
    audio_recovery_rate: float
    overall_recovery_rate: float
    video_stutter_rate: float
    audio_stutter_rate: float
    average_latency_ms: float
    max_latency_ms: float
    video_effective_fps: float
    video_quality_score: float
    audio_quality_score: float
    overall_mos_score: float
    fec_overhead_bps: int


class MetricsCalculator:
    def __init__(self, sim_config: NetworkSimConfig, fec_config: FECConfig):
        self.sim_config = sim_config
        self.fec_config = fec_config

    def calculate_bitrate_series(
        self, trace: PacketTrace, window_ms: float = 100.0, use_fec: bool = True
    ) -> pd.DataFrame:
        cfg = self.sim_config
        duration = cfg.simulation_duration_sec
        window_sec = window_ms / 1000.0
        num_windows = int(np.ceil(duration / window_sec))
        window_edges = np.arange(num_windows + 1) * window_sec
        window_centers = (window_edges[:-1] + window_edges[1:]) / 2

        if use_fec and len(trace.is_recovered) > 0:
            effective_mask = ~trace.is_lost | trace.is_recovered
        else:
            effective_mask = ~trace.is_lost

        v_mask = trace.is_video & effective_mask
        a_mask = ~trace.is_video & effective_mask

        def _bin_bitrate(timestamps, sizes):
            if len(timestamps) == 0:
                return np.zeros(num_windows)
            bin_indices = np.digitize(timestamps, window_edges) - 1
            bin_indices = np.clip(bin_indices, 0, num_windows - 1)
            binned = np.bincount(bin_indices, weights=sizes, minlength=num_windows)
            return (binned * 8) / window_sec

        video_bitrate = _bin_bitrate(trace.timestamps[v_mask], trace.sizes[v_mask])
        audio_bitrate = _bin_bitrate(trace.timestamps[a_mask], trace.sizes[a_mask])
        total_bitrate = video_bitrate + audio_bitrate

        raw_v_mask = trace.is_video & ~trace.is_lost
        raw_a_mask = ~trace.is_video & ~trace.is_lost
        raw_video_bitrate = _bin_bitrate(trace.timestamps[raw_v_mask], trace.sizes[raw_v_mask])
        raw_audio_bitrate = _bin_bitrate(trace.timestamps[raw_a_mask], trace.sizes[raw_a_mask])
        raw_total_bitrate = raw_video_bitrate + raw_audio_bitrate

        ideal_video_bitrate = np.full(num_windows, cfg.video_bitrate_bps)
        ideal_audio_bitrate = np.full(num_windows, cfg.audio_bitrate_bps)
        ideal_total_bitrate = ideal_video_bitrate + ideal_audio_bitrate

        df = pd.DataFrame({
            "time_sec": window_centers,
            "video_bitrate_bps": video_bitrate,
            "audio_bitrate_bps": audio_bitrate,
            "total_bitrate_bps": total_bitrate,
            "raw_video_bitrate_bps": raw_video_bitrate,
            "raw_audio_bitrate_bps": raw_audio_bitrate,
            "raw_total_bitrate_bps": raw_total_bitrate,
            "ideal_video_bitrate_bps": ideal_video_bitrate,
            "ideal_audio_bitrate_bps": ideal_audio_bitrate,
            "ideal_total_bitrate_bps": ideal_total_bitrate,
        })
        return df

    def calculate_stutter_metrics(self, bitrate_df: pd.DataFrame) -> Dict[str, float]:
        cfg = self.sim_config
        threshold_ratio = 0.5

        video_stutter = bitrate_df["video_bitrate_bps"] < (cfg.video_bitrate_bps * threshold_ratio)
        audio_stutter = bitrate_df["audio_bitrate_bps"] < (cfg.audio_bitrate_bps * threshold_ratio)

        video_stutter_rate = float(np.mean(video_stutter))
        audio_stutter_rate = float(np.mean(audio_stutter))

        return {
            "video_stutter_rate": video_stutter_rate,
            "audio_stutter_rate": audio_stutter_rate,
        }

    def calculate_latency_metrics(self, trace: PacketTrace) -> Dict[str, float]:
        cfg = self.sim_config
        base_latency_ms = 20.0
        jitter_base_ms = 5.0

        if len(trace.is_recovered) > 0:
            recovered_packets = trace.is_recovered
            num_recovered = int(np.sum(recovered_packets))
            recovery_delay_ms = ((self.fec_config.fec_ratio_n - 1) * 1000.0 / cfg.video_fps)
            extra_latency = np.where(recovered_packets, recovery_delay_ms, 0)
        else:
            num_recovered = 0
            extra_latency = np.zeros_like(trace.timestamps)

        lost_mask = trace.is_lost
        if len(trace.is_recovered) > 0:
            lost_mask = trace.is_lost & ~trace.is_recovered

        retransmit_delay_ms = 80.0
        retransmit_latency = np.where(lost_mask, retransmit_delay_ms, 0)

        total_packets = len(trace.timestamps)
        random_jitter = np.random.normal(0, jitter_base_ms, total_packets)
        latencies = base_latency_ms + np.abs(random_jitter) + extra_latency + retransmit_latency

        return {
            "average_latency_ms": float(np.mean(latencies)),
            "max_latency_ms": float(np.max(latencies)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
        }

    def calculate_effective_fps(self, trace: PacketTrace) -> float:
        cfg = self.sim_config
        v_mask = trace.is_video
        if len(trace.is_recovered) > 0:
            effective_mask = ~trace.is_lost | trace.is_recovered
        else:
            effective_mask = ~trace.is_lost
        effective_video_packets = np.sum(v_mask & effective_mask)
        total_video_packets = np.sum(v_mask)
        if total_video_packets == 0:
            return 0.0
        return float(cfg.video_fps * effective_video_packets / total_video_packets)

    def calculate_quality_scores(
        self,
        recovery_stats: dict,
        stutter_metrics: dict,
        latency_metrics: dict,
        effective_fps: float,
    ) -> Dict[str, float]:
        cfg = self.sim_config

        overall_recovery = recovery_stats["recovery_rate"]
        v_recovery = recovery_stats["video"]["recovery_rate"]
        a_recovery = recovery_stats["audio"]["recovery_rate"]

        v_stutter = stutter_metrics["video_stutter_rate"]
        a_stutter = stutter_metrics["audio_stutter_rate"]
        avg_latency = latency_metrics["average_latency_ms"]

        fps_ratio = effective_fps / cfg.video_fps if cfg.video_fps > 0 else 0

        video_quality = (
            v_recovery * 0.4
            + (1 - v_stutter) * 0.35
            + fps_ratio * 0.15
            + max(0, 1 - avg_latency / 400) * 0.1
        )
        video_quality = max(0.0, min(1.0, video_quality))

        audio_quality = (
            a_recovery * 0.5
            + (1 - a_stutter) * 0.3
            + max(0, 1 - avg_latency / 300) * 0.2
        )
        audio_quality = max(0.0, min(1.0, audio_quality))

        mos_score = (video_quality * 0.6 + audio_quality * 0.4) * 4.0 + 1.0
        mos_score = max(1.0, min(5.0, mos_score))

        return {
            "video_quality_score": video_quality,
            "audio_quality_score": audio_quality,
            "overall_mos_score": mos_score,
        }

    def compute_all_metrics(
        self, trace: PacketTrace, recovery_stats: dict, bitrate_df: pd.DataFrame
    ) -> QoSMetrics:
        stutter = self.calculate_stutter_metrics(bitrate_df)
        latency = self.calculate_latency_metrics(trace)
        eff_fps = self.calculate_effective_fps(trace)
        quality = self.calculate_quality_scores(recovery_stats, stutter, latency, eff_fps)

        return QoSMetrics(
            video_recovery_rate=recovery_stats["video"]["recovery_rate"],
            audio_recovery_rate=recovery_stats["audio"]["recovery_rate"],
            overall_recovery_rate=recovery_stats["recovery_rate"],
            video_stutter_rate=stutter["video_stutter_rate"],
            audio_stutter_rate=stutter["audio_stutter_rate"],
            average_latency_ms=latency["average_latency_ms"],
            max_latency_ms=latency["max_latency_ms"],
            video_effective_fps=eff_fps,
            video_quality_score=quality["video_quality_score"],
            audio_quality_score=quality["audio_quality_score"],
            overall_mos_score=quality["overall_mos_score"],
            fec_overhead_bps=self.fec_config.fec_overhead_bps,
        )
