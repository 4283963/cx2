from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class NetworkBlockageEvent(BaseModel):
    event_id: int
    start_time_sec: float
    end_time_sec: float
    duration_sec: float
    description: str = "网络彻底阻断 - 隧道/电梯模式"


class SimulationRequest(BaseModel):
    video_fps: int = Field(default=30, ge=1, le=120, description="视频帧率 (FPS)")
    audio_sample_rate: int = Field(default=48000, ge=8000, le=192000, description="音频采样率 (Hz)")
    video_bitrate_bps: int = Field(default=2000000, ge=100000, le=20000000, description="视频码率 (bps)")
    audio_bitrate_bps: int = Field(default=128000, ge=8000, le=1000000, description="音频码率 (bps)")
    packet_loss_rate: float = Field(default=0.05, ge=0.0, le=0.95, description="网络丢包率 (0-1)")
    burst_loss_prob: float = Field(default=0.3, ge=0.0, le=1.0, description="突发丢包概率 (0-1)")
    burst_max_length: int = Field(default=5, ge=1, le=50, description="最大突发丢包长度")
    simulation_duration_sec: float = Field(default=10.0, ge=1.0, le=120.0, description="仿真时长 (秒)")
    fec_type: str = Field(default="RS", description="FEC类型: XOR, RS, INTERLEAVED")
    fec_ratio_k: int = Field(default=4, ge=1, le=20, description="FEC K值 (数据块数量)")
    fec_ratio_n: int = Field(default=5, ge=2, le=30, description="FEC N值 (总块数量，必须>K)")
    random_seed: Optional[int] = Field(default=42, description="随机种子，用于结果复现")
    network_profile: str = Field(default="NORMAL", description="网络场景: NORMAL(正常), TUNNEL(隧道/电梯突变模式)")
    blockage_window_count: int = Field(default=5, ge=1, le=50, description="突变模式下连续完全丢包的时间窗口数量")
    blockage_window_ms: int = Field(default=500, ge=100, le=5000, description="每个阻断时间窗口长度(ms)")


class RecoveryStats(BaseModel):
    total_packets: int
    total_lost: int
    total_recovered: int
    remaining_lost: int
    raw_loss_rate: float
    effective_loss_rate: float
    recovery_rate: float
    video: Dict[str, float]
    audio: Dict[str, float]


class QoSMetricsData(BaseModel):
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


class BitratePoint(BaseModel):
    time_sec: float
    video_bitrate_bps: float
    audio_bitrate_bps: float
    total_bitrate_bps: float
    raw_video_bitrate_bps: float
    raw_audio_bitrate_bps: float
    raw_total_bitrate_bps: float
    ideal_video_bitrate_bps: float
    ideal_audio_bitrate_bps: float
    ideal_total_bitrate_bps: float


class SimulationResponse(BaseModel):
    request: SimulationRequest
    recovery_stats: RecoveryStats
    qos_metrics: QoSMetricsData
    bitrate_series: List[BitratePoint]
    blockage_events: List[NetworkBlockageEvent]
