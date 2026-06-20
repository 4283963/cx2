import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

function createBlockagePlugin(bitrateSeries, blockageEvents) {
  const timeValues = bitrateSeries.map(p => p.time_sec);
  const numPoints = timeValues.length;
  const xIndexOf = (t) => {
    let lo = 0, hi = numPoints - 1, ans = 0;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (timeValues[mid] <= t) { ans = mid; lo = mid + 1; }
      else hi = mid - 1;
    }
    return ans;
  };

  return {
    id: 'blockageOverlay',
    beforeDatasetsDraw(chart) {
      if (!blockageEvents || blockageEvents.length === 0) return;
      const { ctx, chartArea: area, scales: { x, y } } = chart;
      if (!area) return;

      ctx.save();

      blockageEvents.forEach((ev, idx) => {
        const xLeft = x.getPixelForValue(xIndexOf(ev.start_time_sec));
        const xRight = x.getPixelForValue(xIndexOf(ev.end_time_sec));
        const drawLeft = Math.max(area.left, xLeft);
        const drawRight = Math.min(area.right, xRight);
        const drawWidth = Math.max(1, drawRight - drawLeft);

        const gradient = ctx.createLinearGradient(drawLeft, area.top, drawLeft, area.bottom);
        gradient.addColorStop(0, 'rgba(239, 68, 68, 0.05)');
        gradient.addColorStop(0.5, 'rgba(239, 68, 68, 0.20)');
        gradient.addColorStop(1, 'rgba(239, 68, 68, 0.05)');

        ctx.fillStyle = gradient;
        ctx.fillRect(drawLeft, area.top, drawWidth, area.bottom - area.top);

        ctx.strokeStyle = 'rgba(239, 68, 68, 0.85)';
        ctx.lineWidth = 2;
        ctx.setLineDash([6, 4]);
        ctx.beginPath();
        ctx.moveTo(drawLeft, area.top);
        ctx.lineTo(drawLeft, area.bottom);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(drawRight, area.top);
        ctx.lineTo(drawRight, area.bottom);
        ctx.stroke();
        ctx.setLineDash([]);

        if (idx === 0 || Math.abs(ev.start_time_sec - blockageEvents[idx - 1].end_time_sec) > 0.15) {
          const label = '🚫 网络彻底阻断';
          ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, sans-serif';
          const labelMetrics = ctx.measureText(label);
          const labelW = labelMetrics.width + 20;
          const labelH = 24;
          const centerX = (drawLeft + drawRight) / 2;
          const labelX = Math.max(area.left + 4, Math.min(area.right - labelW - 4, centerX - labelW / 2));
          const labelY = area.top + 10;

          ctx.fillStyle = 'rgba(127, 29, 29, 0.92)';
          ctx.beginPath();
          const r = 6;
          ctx.moveTo(labelX + r, labelY);
          ctx.lineTo(labelX + labelW - r, labelY);
          ctx.quadraticCurveTo(labelX + labelW, labelY, labelX + labelW, labelY + r);
          ctx.lineTo(labelX + labelW, labelY + labelH - r);
          ctx.quadraticCurveTo(labelX + labelW, labelY + labelH, labelX + labelW - r, labelY + labelH);
          ctx.lineTo(labelX + r, labelY + labelH);
          ctx.quadraticCurveTo(labelX, labelY + labelH, labelX, labelY + labelH - r);
          ctx.lineTo(labelX, labelY + r);
          ctx.quadraticCurveTo(labelX, labelY, labelX + r, labelY);
          ctx.closePath();
          ctx.fill();

          ctx.strokeStyle = 'rgba(248, 113, 113, 0.9)';
          ctx.lineWidth = 1.5;
          ctx.stroke();

          ctx.fillStyle = '#fecaca';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(label, labelX + labelW / 2, labelY + labelH / 2);
          ctx.textAlign = 'start';
          ctx.textBaseline = 'alphabetic';
        }
      });

      ctx.restore();
    },
  };
}

function buildChartOptions(title, yLabel, bitrateSeries, blockageEvents) {
  const timeValues = bitrateSeries.map(p => p.time_sec);
  const plugin = blockageEvents && blockageEvents.length > 0
    ? [createBlockagePlugin(bitrateSeries, blockageEvents)]
    : [];

  return {
    responsive: true,
    maintainAspectRatio: true,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#cbd5e1',
          usePointStyle: true,
          padding: 16,
          font: { size: 12 },
        },
      },
      title: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#f1f5f9',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(100, 116, 139, 0.3)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
      },
    },
    scales: {
      x: {
        type: 'linear',
        min: timeValues[0],
        max: timeValues[timeValues.length - 1],
        title: {
          display: true,
          text: '时间 (秒)',
          color: '#94a3b8',
          font: { size: 12 },
        },
        ticks: {
          color: '#64748b',
          maxTicksLimit: 10,
          callback: (v) => Number(v).toFixed(1),
        },
        grid: {
          color: 'rgba(100, 116, 139, 0.1)',
        },
      },
      y: {
        title: {
          display: true,
          text: yLabel,
          color: '#94a3b8',
          font: { size: 12 },
        },
        ticks: {
          color: '#64748b',
          callback: function (value) {
            if (value >= 1) return value.toFixed(1) + ' Mbps';
            if (value >= 0.001) return (value * 1000).toFixed(0) + ' kbps';
            return value + ' bps';
          },
        },
        grid: {
          color: 'rgba(100, 116, 139, 0.1)',
        },
      },
    },
    _plugins: plugin,
  };
}

function bpsToMbps(series, key) {
  return series.map(p => ({ x: p.time_sec, y: p[key] / 1000000 }));
}

export default function BitrateChart({ bitrateSeries, blockageEvents }) {
  if (!bitrateSeries || bitrateSeries.length === 0) {
    return null;
  }

  const totalData = useMemo(() => ({
    datasets: [
      {
        label: '理想码率',
        data: bpsToMbps(bitrateSeries, 'ideal_total_bitrate_bps'),
        borderColor: '#64748b',
        backgroundColor: 'rgba(100, 116, 139, 0.1)',
        borderDash: [8, 4],
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: '无补偿码率',
        data: bpsToMbps(bitrateSeries, 'raw_total_bitrate_bps'),
        borderColor: '#f87171',
        backgroundColor: 'rgba(248, 113, 113, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
        fill: false,
      },
      {
        label: 'FEC补偿后码率',
        data: bpsToMbps(bitrateSeries, 'total_bitrate_bps'),
        borderColor: '#4ade80',
        backgroundColor: 'rgba(74, 222, 128, 0.15)',
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.3,
        fill: true,
      },
    ],
  }), [bitrateSeries]);

  const videoData = useMemo(() => ({
    datasets: [
      {
        label: '理想视频码率',
        data: bpsToMbps(bitrateSeries, 'ideal_video_bitrate_bps'),
        borderColor: '#64748b',
        borderDash: [8, 4],
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: '无补偿视频码率',
        data: bpsToMbps(bitrateSeries, 'raw_video_bitrate_bps'),
        borderColor: '#fb923c',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: 'FEC补偿视频码率',
        data: bpsToMbps(bitrateSeries, 'video_bitrate_bps'),
        borderColor: '#60a5fa',
        backgroundColor: 'rgba(96, 165, 250, 0.1)',
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.3,
        fill: true,
      },
    ],
  }), [bitrateSeries]);

  const audioData = useMemo(() => ({
    datasets: [
      {
        label: '理想音频码率',
        data: bpsToMbps(bitrateSeries, 'ideal_audio_bitrate_bps'),
        borderColor: '#64748b',
        borderDash: [8, 4],
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: '无补偿音频码率',
        data: bpsToMbps(bitrateSeries, 'raw_audio_bitrate_bps'),
        borderColor: '#f472b6',
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: 'FEC补偿音频码率',
        data: bpsToMbps(bitrateSeries, 'audio_bitrate_bps'),
        borderColor: '#a78bfa',
        backgroundColor: 'rgba(167, 139, 250, 0.1)',
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.3,
        fill: true,
      },
    ],
  }), [bitrateSeries]);

  const totalOpts = useMemo(() => {
    const opts = buildChartOptions('总码率对比', '总码率', bitrateSeries, blockageEvents);
    const plugins = opts._plugins || [];
    delete opts._plugins;
    return { ...opts, plugins: { ...opts.plugins, _local: plugins } };
  }, [bitrateSeries, blockageEvents]);

  const videoOpts = useMemo(() => {
    const opts = buildChartOptions('视频码率对比', '视频码率', bitrateSeries, blockageEvents);
    const plugins = opts._plugins || [];
    delete opts._plugins;
    return { ...opts, plugins: { ...opts.plugins, _local: plugins } };
  }, [bitrateSeries, blockageEvents]);

  const audioOpts = useMemo(() => {
    const opts = buildChartOptions('音频码率对比', '音频码率', bitrateSeries, blockageEvents);
    const plugins = opts._plugins || [];
    delete opts._plugins;
    return { ...opts, plugins: { ...opts.plugins, _local: plugins } };
  }, [bitrateSeries, blockageEvents]);

  const totalPlugins = totalOpts.plugins._local || [];
  const videoPlugins = videoOpts.plugins._local || [];
  const audioPlugins = audioOpts.plugins._local || [];
  delete totalOpts.plugins._local;
  delete videoOpts.plugins._local;
  delete audioOpts.plugins._local;

  return (
    <>
      <div className="chart-container">
        <h3>📊 总码率曲线对比 (补偿前后)</h3>
        <Line data={totalData} options={totalOpts} plugins={totalPlugins} height={100} />
      </div>

      <div className="chart-container">
        <h3>🎬 视频码率曲线对比</h3>
        <Line data={videoData} options={videoOpts} plugins={videoPlugins} height={80} />
      </div>

      <div className="chart-container">
        <h3>🎵 音频码率曲线对比</h3>
        <Line data={audioData} options={audioOpts} plugins={audioPlugins} height={80} />
      </div>
    </>
  );
}
