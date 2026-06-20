import React, { useState } from 'react';
import ControlPanel from './components/ControlPanel.jsx';
import BitrateChart from './components/BitrateChart.jsx';
import MetricsDisplay from './components/MetricsDisplay.jsx';
import { runSimulation } from './services/api.js';

const DEFAULT_PARAMS = {
  video_fps: 30,
  audio_sample_rate: 48000,
  video_bitrate_bps: 2000000,
  audio_bitrate_bps: 128000,
  packet_loss_rate: 0.05,
  burst_loss_prob: 0.3,
  burst_max_length: 5,
  simulation_duration_sec: 10.0,
  fec_type: 'RS',
  fec_ratio_k: 4,
  fec_ratio_n: 5,
  random_seed: 42,
};

export default function App() {
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runSimulation(params);
      setResult(data);
    } catch (err) {
      setError(err.message || '仿真运行失败，请检查后端服务是否启动');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🎥 音视频会议丢包补偿模拟评估工具</h1>
        <p>基于 FEC 前向纠错模型 · 网络丢包仿真 · QoE 质量评估</p>
      </header>

      <div className="main-grid">
        <div>
          <ControlPanel
            params={params}
            setParams={setParams}
            onRun={handleRun}
            loading={loading}
          />
        </div>

        <div className="charts-section">
          {error && (
            <div className="panel" style={{ borderColor: '#f87171' }}>
              <div style={{ color: '#f87171', fontWeight: 600 }}>❌ {error}</div>
            </div>
          )}

          {!result && !loading && !error && (
            <div className="panel">
              <div className="empty-state">
                <div className="empty-state-icon">📡</div>
                <div className="empty-state-text">
                  请在左侧配置仿真参数后，点击「运行仿真」按钮开始评估
                </div>
              </div>
            </div>
          )}

          {result && (
            <div className="panel">
              <h2 className="panel-title">仿真结果评估</h2>
              <MetricsDisplay
                recoveryStats={result.recovery_stats}
                qosMetrics={result.qos_metrics}
              />
              <BitrateChart bitrateSeries={result.bitrate_series} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
