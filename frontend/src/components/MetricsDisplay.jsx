import React from 'react';

function classify(value, thresholds) {
  if (value >= thresholds.good) return 'good';
  if (value >= thresholds.warn) return 'warn';
  return 'bad';
}

function classifyInverse(value, thresholds) {
  if (value <= thresholds.good) return 'good';
  if (value <= thresholds.warn) return 'warn';
  return 'bad';
}

function MetricCard({ label, value, unit, percent, thresholds, inverse }) {
  const quality = inverse
    ? classifyInverse(value, thresholds)
    : classify(value, thresholds);

  const barColor = {
    good: 'linear-gradient(90deg, #4ade80, #22c55e)',
    warn: 'linear-gradient(90deg, #fbbf24, #f59e0b)',
    bad: 'linear-gradient(90deg, #f87171, #ef4444)',
  }[quality];

  const displayPercent = percent !== undefined ? Math.min(100, Math.max(0, percent)) : null;

  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${quality}`}>
        {typeof value === 'number' ? value.toFixed(value < 10 ? 2 : 0) : value}
        {unit && <span className="metric-unit">{unit}</span>}
      </div>
      {displayPercent !== null && (
        <div className="metric-bar">
          <div
            className="metric-bar-fill"
            style={{ width: `${displayPercent}%`, background: barColor }}
          />
        </div>
      )}
    </div>
  );
}

export default function MetricsDisplay({ recoveryStats, qosMetrics }) {
  if (!recoveryStats || !qosMetrics) return null;

  return (
    <>
      <div className="section-label">📈 FEC 恢复效果</div>
      <div className="metrics-grid">
        <MetricCard
          label="总包数"
          value={recoveryStats.total_packets}
          unit=""
          thresholds={{ good: 100, warn: 10 }}
        />
        <MetricCard
          label="原始丢包数"
          value={recoveryStats.total_lost}
          unit=""
          inverse
          thresholds={{ good: 10, warn: 50 }}
        />
        <MetricCard
          label="成功恢复"
          value={recoveryStats.total_recovered}
          unit=""
          percent={(recoveryStats.total_recovered / Math.max(1, recoveryStats.total_lost)) * 100}
          thresholds={{ good: 0.8, warn: 0.5 }}
        />
        <MetricCard
          label="原始丢包率"
          value={recoveryStats.raw_loss_rate * 100}
          unit="%"
          inverse
          percent={100 - recoveryStats.raw_loss_rate * 100}
          thresholds={{ good: 0.01, warn: 0.05 }}
        />
        <MetricCard
          label="有效丢包率"
          value={recoveryStats.effective_loss_rate * 100}
          unit="%"
          inverse
          percent={100 - recoveryStats.effective_loss_rate * 100}
          thresholds={{ good: 0.01, warn: 0.05 }}
        />
        <MetricCard
          label="整体恢复率"
          value={qosMetrics.overall_recovery_rate * 100}
          unit="%"
          percent={qosMetrics.overall_recovery_rate * 100}
          thresholds={{ good: 0.8, warn: 0.5 }}
        />
      </div>

      <div className="section-label">🎥 视频质量指标</div>
      <div className="metrics-grid">
        <MetricCard
          label="视频恢复率"
          value={qosMetrics.video_recovery_rate * 100}
          unit="%"
          percent={qosMetrics.video_recovery_rate * 100}
          thresholds={{ good: 0.85, warn: 0.6 }}
        />
        <MetricCard
          label="视频卡顿率"
          value={qosMetrics.video_stutter_rate * 100}
          unit="%"
          inverse
          percent={100 - qosMetrics.video_stutter_rate * 100}
          thresholds={{ good: 0.05, warn: 0.15 }}
        />
        <MetricCard
          label="有效帧率"
          value={qosMetrics.video_effective_fps}
          unit="FPS"
          percent={(qosMetrics.video_effective_fps / 30) * 100}
          thresholds={{ good: 25, warn: 15 }}
        />
        <MetricCard
          label="视频质量分"
          value={qosMetrics.video_quality_score * 100}
          unit="分"
          percent={qosMetrics.video_quality_score * 100}
          thresholds={{ good: 80, warn: 60 }}
        />
      </div>

      <div className="section-label">🔊 音频质量指标</div>
      <div className="metrics-grid">
        <MetricCard
          label="音频恢复率"
          value={qosMetrics.audio_recovery_rate * 100}
          unit="%"
          percent={qosMetrics.audio_recovery_rate * 100}
          thresholds={{ good: 0.9, warn: 0.7 }}
        />
        <MetricCard
          label="音频卡顿率"
          value={qosMetrics.audio_stutter_rate * 100}
          unit="%"
          inverse
          percent={100 - qosMetrics.audio_stutter_rate * 100}
          thresholds={{ good: 0.03, warn: 0.1 }}
        />
        <MetricCard
          label="音频质量分"
          value={qosMetrics.audio_quality_score * 100}
          unit="分"
          percent={qosMetrics.audio_quality_score * 100}
          thresholds={{ good: 85, warn: 65 }}
        />
        <MetricCard
          label="MOS 评分"
          value={qosMetrics.overall_mos_score}
          unit="/ 5.0"
          percent={(qosMetrics.overall_mos_score / 5) * 100}
          thresholds={{ good: 4.0, warn: 3.0 }}
        />
      </div>

      <div className="section-label">⏱️ 延迟与开销</div>
      <div className="metrics-grid">
        <MetricCard
          label="平均延迟"
          value={qosMetrics.average_latency_ms}
          unit="ms"
          inverse
          percent={Math.max(0, 100 - qosMetrics.average_latency_ms / 2)}
          thresholds={{ good: 80, warn: 150 }}
        />
        <MetricCard
          label="最大延迟"
          value={qosMetrics.max_latency_ms}
          unit="ms"
          inverse
          percent={Math.max(0, 100 - qosMetrics.max_latency_ms / 4)}
          thresholds={{ good: 150, warn: 300 }}
        />
        <MetricCard
          label="FEC 开销"
          value={qosMetrics.fec_overhead_bps / 1000}
          unit="kbps"
          inverse
          percent={Math.max(0, 100 - (qosMetrics.fec_overhead_bps / 2000000) * 100)}
          thresholds={{ good: 100, warn: 500 }}
        />
      </div>
    </>
  );
}
