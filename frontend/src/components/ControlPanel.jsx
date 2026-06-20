import React from 'react';

export default function ControlPanel({ params, setParams, onRun, loading }) {
  const handleChange = (key, value) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="panel">
      <h2 className="panel-title">仿真参数配置</h2>

      <div className="section-label">视频参数</div>

      <div className="form-group">
        <label className="form-label">视频帧率 (FPS)</label>
        <div className="form-slider-row">
          <input
            type="range"
            className="form-slider"
            min="1"
            max="60"
            value={params.video_fps}
            onChange={e => handleChange('video_fps', parseInt(e.target.value))}
          />
          <span className="slider-value">{params.video_fps}</span>
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">视频码率 (Mbps)</label>
        <div className="form-slider-row">
          <input
            type="range"
            className="form-slider"
            min="0.1"
            max="10"
            step="0.1"
            value={(params.video_bitrate_bps / 1000000).toFixed(1)}
            onChange={e => handleChange('video_bitrate_bps', Math.round(parseFloat(e.target.value) * 1000000))}
          />
          <span className="slider-value">{(params.video_bitrate_bps / 1000000).toFixed(1)}</span>
        </div>
      </div>

      <div className="section-label">音频参数</div>

      <div className="form-group">
        <label className="form-label">音频采样率 (kHz)</label>
        <select
          className="form-select"
          value={params.audio_sample_rate}
          onChange={e => handleChange('audio_sample_rate', parseInt(e.target.value))}
        >
          <option value="8000">8 kHz (电话音质)</option>
          <option value="16000">16 kHz (宽带语音)</option>
          <option value="32000">32 kHz</option>
          <option value="44100">44.1 kHz (CD音质)</option>
          <option value="48000">48 kHz (专业音质)</option>
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">音频码率 (kbps)</label>
        <div className="form-slider-row">
          <input
            type="range"
            className="form-slider"
            min="8"
            max="320"
            step="8"
            value={Math.round(params.audio_bitrate_bps / 1000)}
            onChange={e => handleChange('audio_bitrate_bps', parseInt(e.target.value) * 1000)}
          />
          <span className="slider-value">{Math.round(params.audio_bitrate_bps / 1000)}</span>
        </div>
      </div>

      <div className="section-label">网络丢包参数</div>

      <div className="form-group">
        <label className="form-label">平均丢包率 (%)</label>
        <div className="form-slider-row">
          <input
            type="range"
            className="form-slider"
            min="0"
            max="50"
            step="0.5"
            value={(params.packet_loss_rate * 100).toFixed(1)}
            onChange={e => handleChange('packet_loss_rate', parseFloat(e.target.value) / 100)}
          />
          <span className="slider-value">{(params.packet_loss_rate * 100).toFixed(1)}%</span>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">突发概率</label>
          <div className="form-slider-row">
            <input
              type="range"
              className="form-slider"
              min="0"
              max="100"
              value={Math.round(params.burst_loss_prob * 100)}
              onChange={e => handleChange('burst_loss_prob', parseInt(e.target.value) / 100)}
            />
            <span className="slider-value">{Math.round(params.burst_loss_prob * 100)}%</span>
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">最大突发长度</label>
          <input
            type="number"
            className="form-input"
            min="1"
            max="50"
            value={params.burst_max_length}
            onChange={e => handleChange('burst_max_length', parseInt(e.target.value) || 1)}
          />
        </div>
      </div>

      <div className="section-label">FEC 纠错参数</div>

      <div className="form-group">
        <label className="form-label">FEC 编码类型</label>
        <select
          className="form-select"
          value={params.fec_type}
          onChange={e => handleChange('fec_type', e.target.value)}
        >
          <option value="XOR">XOR 异或编码 (简单)</option>
          <option value="RS">Reed-Solomon (均衡)</option>
          <option value="INTERLEAVED">交织 RS (抗突发)</option>
        </select>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">数据块 K</label>
          <input
            type="number"
            className="form-input"
            min="1"
            max="20"
            value={params.fec_ratio_k}
            onChange={e => handleChange('fec_ratio_k', parseInt(e.target.value) || 1)}
          />
        </div>
        <div className="form-group">
          <label className="form-label">总块数 N</label>
          <input
            type="number"
            className="form-input"
            min="2"
            max="30"
            value={params.fec_ratio_n}
            onChange={e => handleChange('fec_ratio_n', parseInt(e.target.value) || 2)}
          />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">仿真时长 (秒)</label>
        <div className="form-slider-row">
          <input
            type="range"
            className="form-slider"
            min="1"
            max="60"
            value={params.simulation_duration_sec}
            onChange={e => handleChange('simulation_duration_sec', parseFloat(e.target.value))}
          />
          <span className="slider-value">{params.simulation_duration_sec}s</span>
        </div>
      </div>

      <button
        className="btn-primary"
        onClick={onRun}
        disabled={loading}
      >
        {loading ? '仿真计算中...' : '▶ 运行仿真'}
      </button>
    </div>
  );
}
