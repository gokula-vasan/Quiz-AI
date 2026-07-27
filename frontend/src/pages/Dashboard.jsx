import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { BarChart3, BookOpen, CheckSquare, Award, TrendingUp, AlertTriangle, Flame, CheckCircle } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
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

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const res = await api.get('/progress/dashboard');
        setData(res.data);
      } catch (err) {
        console.error("Dashboard error:", err);
        setError("Failed to fetch dashboard statistics.");
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-100px)] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  const { summary, timeline, strong_topics, weak_topics } = data || {
    summary: { total_documents: 0, total_quizzes: 0, total_attempts: 0, overall_accuracy: 0, study_streak: 0 },
    timeline: [],
    strong_topics: [],
    weak_topics: []
  };

  const chartData = {
    labels: timeline.map(t => {
      const d = new Date(t.date);
      if (isNaN(d.getTime())) return t.date;
      const formattedDate = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      const formattedTime = d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });
      return `${formattedDate}, ${formattedTime}`;
    }),
    datasets: [
      {
        fill: true,
        label: 'Accuracy (%)',
        data: timeline.map(t => t.percentage),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.05)',
        tension: 0.4,
        pointBackgroundColor: '#818cf8',
        pointBorderColor: '#0e1626',
        pointHoverRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        padding: 12,
        backgroundColor: '#0f172a',
        borderColor: '#1e293b',
        borderWidth: 1,
        titleColor: '#94a3b8',
        bodyColor: '#fff',
        displayColors: false,
      }
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        grid: { color: 'rgba(51, 65, 85, 0.15)' },
        ticks: {
          color: '#64748b',
          callback: (value) => `${value}%`
        }
      },
      x: {
        grid: { display: false },
        ticks: {
          color: '#64748b',
          maxRotation: 45,
          minRotation: 45,
        }
      }
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Learning Dashboard</h1>
          <p className="text-slate-400 mt-1">Track your autonomous multi-agent quiz progress and metrics</p>
        </div>
        <button
          onClick={() => navigate('/upload')}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-bold shadow-lg shadow-indigo-500/25 transition-all text-sm shrink-0"
        >
          Add Study Material
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10 text-indigo-400">
            <BookOpen size={48} />
          </div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Materials</span>
          <h3 className="text-2xl font-black text-white mt-1">{summary.total_documents}</h3>
          <p className="text-[10px] text-slate-400 mt-1">Uploaded PDFs</p>
        </div>

        <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10 text-purple-400">
            <CheckSquare size={48} />
          </div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Generated Quizzes</span>
          <h3 className="text-2xl font-black text-white mt-1">{summary.total_quizzes}</h3>
          <p className="text-[10px] text-slate-400 mt-1">Ready for study</p>
        </div>

        <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10 text-teal-400">
            <Award size={48} />
          </div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Attempts</span>
          <h3 className="text-2xl font-black text-white mt-1">{summary.total_attempts}</h3>
          <p className="text-[10px] text-slate-400 mt-1">Taken quizzes</p>
        </div>

        <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-15 text-orange-500">
            <Flame size={48} />
          </div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Study Streak</span>
          <h3 className="text-2xl font-black text-orange-400 mt-1">{summary.study_streak} Days</h3>
          <p className="text-[10px] text-slate-450 mt-1">Consecutive learning</p>
        </div>

        <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10 text-amber-400">
            <TrendingUp size={48} />
          </div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Overall Accuracy</span>
          <h3 className="text-2xl font-black text-white mt-1">{summary.overall_accuracy}%</h3>
          <p className="text-[10px] text-slate-400 mt-1">Average correction score</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md flex flex-col shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-200">Performance Tracking</h2>
            <span className="text-xs font-semibold text-indigo-400">Score History</span>
          </div>
          
          <div className="flex-1 w-full min-h-[300px] mt-4">
            {timeline.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500">
                <BarChart3 size={40} className="mb-2 opacity-50" />
                <span className="text-sm">Complete a quiz to view performance tracking charts</span>
              </div>
            ) : (
              <Line data={chartData} options={chartOptions} />
            )}
          </div>
        </div>

        <div className="lg:col-span-1 space-y-6 flex flex-col">
          {/* Strong Topics List */}
          <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-xl flex-1 flex flex-col">
            <h2 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <CheckCircle size={18} className="text-emerald-400" />
              <span>Strong Topics</span>
            </h2>

            {strong_topics.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-500 border border-dashed border-slate-800/80 rounded-xl">
                <Award size={32} className="text-slate-650 mb-2 opacity-40" />
                <h4 className="text-sm font-semibold text-slate-450">Mastery Awaiting</h4>
                <p className="text-xs text-slate-500 mt-1">Score {'>='} 75% on quiz topics to view strengths here.</p>
              </div>
            ) : (
              <div className="space-y-3 flex-1 overflow-y-auto">
                {strong_topics.map((topic, idx) => (
                  <div key={idx} className="p-3 bg-slate-900/40 border border-slate-800/80 rounded-xl flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-300">{topic}</span>
                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                      ✓ Mastered
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Weak Topics List */}
          <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-xl flex-1 flex flex-col">
            <h2 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
              <AlertTriangle size={18} className="text-amber-500" />
              <span>Weak Topics</span>
            </h2>

            {weak_topics.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-500 border border-dashed border-slate-800/80 rounded-xl">
                <Award size={32} className="text-emerald-500 mb-2" />
                <h4 className="text-sm font-semibold text-slate-300">Perfect Record!</h4>
                <p className="text-xs text-slate-500 mt-1">No weak areas identified or quiz attempts yet.</p>
              </div>
            ) : (
              <div className="space-y-3 flex-1 overflow-y-auto">
                {weak_topics.map((topic, idx) => (
                  <div key={idx} className="p-3 bg-slate-900/40 border border-slate-800/80 rounded-xl flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-300">{topic}</span>
                    <span className="text-[10px] font-bold text-amber-500 bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20">
                      Needs Practice
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
