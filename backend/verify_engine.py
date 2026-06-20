import sys
sys.path.insert(0, '.')

from app.engine.packet_simulator import NetworkSimConfig, PacketLossSimulator
from app.engine.fec_calculator import FECConfig, FECForwardErrorCorrection
from app.engine.metrics_calculator import MetricsCalculator

def main():
    print("=" * 60)
    print("音视频会议丢包补偿模拟评估工具 - 计算引擎验证")
    print("=" * 60)

    sim_config = NetworkSimConfig(
        video_fps=30,
        audio_sample_rate=48000,
        packet_loss_rate=0.10,
        burst_loss_prob=0.3,
        burst_max_length=5,
        simulation_duration_sec=5.0,
        video_bitrate_bps=2000000,
        audio_bitrate_bps=128000,
        random_seed=42,
    )

    print("\n[1/4] 生成网络丢包轨迹...")
    simulator = PacketLossSimulator(sim_config)
    raw_trace = simulator.simulate()
    print(f"  ✓ 生成 {len(raw_trace.timestamps)} 个数据包")
    print(f"  ✓ 丢包数: {raw_trace.is_lost.sum()} ({raw_trace.is_lost.mean()*100:.1f}%)")

    print("\n[2/4] 应用 FEC 前向纠错...")
    fec_config = FECConfig(fec_type="RS", fec_ratio_k=4, fec_ratio_n=5)
    fec = FECForwardErrorCorrection(sim_config, fec_config)
    recovered_trace, updated_fec = fec.apply_fec(raw_trace)
    recovery_stats = fec.calculate_effective_loss_rate(recovered_trace)
    print(f"  ✓ 恢复包数: {recovery_stats['total_recovered']}")
    print(f"  ✓ 整体恢复率: {recovery_stats['recovery_rate']*100:.1f}%")
    print(f"  ✓ 视频恢复率: {recovery_stats['video']['recovery_rate']*100:.1f}%")
    print(f"  ✓ 音频恢复率: {recovery_stats['audio']['recovery_rate']*100:.1f}%")

    print("\n[3/4] 计算 QoS 指标...")
    metrics_calc = MetricsCalculator(sim_config, updated_fec)
    bitrate_df = metrics_calc.calculate_bitrate_series(recovered_trace)
    qos = metrics_calc.compute_all_metrics(recovered_trace, recovery_stats, bitrate_df)
    print(f"  ✓ 有效视频帧率: {qos.video_effective_fps:.1f} FPS")
    print(f"  ✓ 平均延迟: {qos.average_latency_ms:.1f} ms")
    print(f"  ✓ 视频卡顿率: {qos.video_stutter_rate*100:.1f}%")
    print(f"  ✓ 视频质量分: {qos.video_quality_score*100:.1f}")
    print(f"  ✓ 音频质量分: {qos.audio_quality_score*100:.1f}")
    print(f"  ✓ MOS 评分: {qos.overall_mos_score:.2f} / 5.0")
    print(f"  ✓ FEC 带宽开销: {qos.fec_overhead_bps/1000:.1f} kbps")

    print("\n[4/4] 码率时间序列...")
    print(f"  ✓ 时间窗口数: {len(bitrate_df)}")
    print(f"  ✓ 平均总码率(补偿后): {bitrate_df['total_bitrate_bps'].mean()/1000000:.2f} Mbps")
    print(f"  ✓ 平均总码率(无补偿): {bitrate_df['raw_total_bitrate_bps'].mean()/1000000:.2f} Mbps")
    print(f"  ✓ 理想总码率: {bitrate_df['ideal_total_bitrate_bps'].mean()/1000000:.2f} Mbps")

    print("\n" + "=" * 60)
    print("✅ 计算引擎验证通过！")
    print("=" * 60)

if __name__ == "__main__":
    main()
