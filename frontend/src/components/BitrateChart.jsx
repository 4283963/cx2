import React from 'react';
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

function buildChartOptions(title, yLabel) {
  return {
    responsive: true,
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
        title: {
          display: true,
          text: '时间 (秒)',
          color: '#94a3b8',
          font: { size: 12 },
        },
        ticks: {
          color: '#64748b',
          maxTicksLimit: 10,
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
            if (value >= 1000000) return (value / 1000000).toFixed(1) + ' Mbps';
            if (value >= 1000) return (value / 1000).toFixed(0) + ' kbps';
            return value + ' bps';
          },
        },
        grid: {
          color: 'rgba(100, 116, 139, 0.1)',
        },
      },
    },
  };
}

function bpsToMbps(series, key) {
  return series.map(p => p[key] / 1000000);
}

export default function BitrateChart({ bitrateSeries }) {
  if (!bitrateSeries || bitrateSeries.length === 0) {
    return null;
  }

  const labels = bitrateSeries.map(p => p.time_sec.toFixed(1));

  const totalData = {
    labels,
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
  };

  const videoData = {
    labels,
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
  };

  const audioData = {
    labels,
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
  };

  const totalOptions = buildChartOptions('总码率对比', '总码率');
  const videoOptions = buildChartOptions('视频码率对比', '视频码率');
  const audioOptions = buildChartOptions('音频码率对比', '音频码率');

  return (
    <>
      <div className="chart-container">
        <h3>📊 总码率曲线对比 (补偿前后)</h3>
        <Line data={totalData} options={totalOptions} height={100} />
      </div>

      <div className="chart-container">
        <h3>🎬 视频码率曲线对比</h3>
        <Line data={videoData} options={videoOptions} height={80} />
      </div>

      <div className="chart-container">
        <h3>🎵 音频码率曲线对比</h3>
        <Line data={audioData} options={audioOptions} height={80} />
      </div>
    </>
  );
}
