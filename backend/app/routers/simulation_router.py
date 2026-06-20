from fastapi import APIRouter
from ..models.schemas import SimulationRequest, SimulationResponse, RecoveryStats, QoSMetricsData, BitratePoint
from ..engine.packet_simulator import NetworkSimConfig, PacketLossSimulator
from ..engine.fec_calculator import FECConfig, FECForwardErrorCorrection
from ..engine.metrics_calculator import MetricsCalculator


router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "packet-loss-simulator"}


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest):
    sim_config = NetworkSimConfig(
        video_fps=request.video_fps,
        audio_sample_rate=request.audio_sample_rate,
        packet_loss_rate=request.packet_loss_rate,
        burst_loss_prob=request.burst_loss_prob,
        burst_max_length=request.burst_max_length,
        simulation_duration_sec=request.simulation_duration_sec,
        video_bitrate_bps=request.video_bitrate_bps,
        audio_bitrate_bps=request.audio_bitrate_bps,
        random_seed=request.random_seed,
    )

    simulator = PacketLossSimulator(sim_config)
    raw_trace = simulator.simulate()

    fec_config = FECConfig(
        fec_type=request.fec_type,
        fec_ratio_k=request.fec_ratio_k,
        fec_ratio_n=max(request.fec_ratio_n, request.fec_ratio_k + 1),
    )

    fec = FECForwardErrorCorrection(sim_config, fec_config)
    recovered_trace, _ = fec.apply_fec(raw_trace)

    recovery_stats_dict = fec.calculate_effective_loss_rate(recovered_trace)

    metrics_calc = MetricsCalculator(sim_config, fec_config)
    bitrate_df = metrics_calc.calculate_bitrate_series(recovered_trace)
    qos_metrics_obj = metrics_calc.compute_all_metrics(
        recovered_trace, recovery_stats_dict, bitrate_df
    )

    recovery_stats = RecoveryStats(
        total_packets=recovery_stats_dict["total_packets"],
        total_lost=recovery_stats_dict["total_lost"],
        total_recovered=recovery_stats_dict["total_recovered"],
        remaining_lost=recovery_stats_dict["remaining_lost"],
        raw_loss_rate=recovery_stats_dict["raw_loss_rate"],
        effective_loss_rate=recovery_stats_dict["effective_loss_rate"],
        recovery_rate=recovery_stats_dict["recovery_rate"],
        video={
            "lost": float(recovery_stats_dict["video"]["lost"]),
            "recovered": float(recovery_stats_dict["video"]["recovered"]),
            "recovery_rate": recovery_stats_dict["video"]["recovery_rate"],
        },
        audio={
            "lost": float(recovery_stats_dict["audio"]["lost"]),
            "recovered": float(recovery_stats_dict["audio"]["recovered"]),
            "recovery_rate": recovery_stats_dict["audio"]["recovery_rate"],
        },
    )

    qos_metrics = QoSMetricsData(
        video_recovery_rate=qos_metrics_obj.video_recovery_rate,
        audio_recovery_rate=qos_metrics_obj.audio_recovery_rate,
        overall_recovery_rate=qos_metrics_obj.overall_recovery_rate,
        video_stutter_rate=qos_metrics_obj.video_stutter_rate,
        audio_stutter_rate=qos_metrics_obj.audio_stutter_rate,
        average_latency_ms=qos_metrics_obj.average_latency_ms,
        max_latency_ms=qos_metrics_obj.max_latency_ms,
        video_effective_fps=qos_metrics_obj.video_effective_fps,
        video_quality_score=qos_metrics_obj.video_quality_score,
        audio_quality_score=qos_metrics_obj.audio_quality_score,
        overall_mos_score=qos_metrics_obj.overall_mos_score,
        fec_overhead_bps=qos_metrics_obj.fec_overhead_bps,
    )

    bitrate_series = []
    for _, row in bitrate_df.iterrows():
        bitrate_series.append(
            BitratePoint(
                time_sec=float(row["time_sec"]),
                video_bitrate_bps=float(row["video_bitrate_bps"]),
                audio_bitrate_bps=float(row["audio_bitrate_bps"]),
                total_bitrate_bps=float(row["total_bitrate_bps"]),
                raw_video_bitrate_bps=float(row["raw_video_bitrate_bps"]),
                raw_audio_bitrate_bps=float(row["raw_audio_bitrate_bps"]),
                raw_total_bitrate_bps=float(row["raw_total_bitrate_bps"]),
                ideal_video_bitrate_bps=float(row["ideal_video_bitrate_bps"]),
                ideal_audio_bitrate_bps=float(row["ideal_audio_bitrate_bps"]),
                ideal_total_bitrate_bps=float(row["ideal_total_bitrate_bps"]),
            )
        )

    return SimulationResponse(
        request=request,
        recovery_stats=recovery_stats,
        qos_metrics=qos_metrics,
        bitrate_series=bitrate_series,
    )
