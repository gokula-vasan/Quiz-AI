import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, UploadCloud, BarChart3 } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  if (!user) return null;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="border-b border-slate-800 bg-[#0e1626]/85 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
          Q
        </div>
        <span className="font-extrabold text-xl bg-gradient-to-r from-white via-indigo-200 to-purple-400 bg-clip-text text-transparent">
          QuizMaster AI
        </span>
      </div>

      <div className="flex items-center gap-6">
        <Link
          to="/"
          className={`flex items-center gap-2 text-sm font-medium transition-all ${
            isActive('/') 
              ? 'text-indigo-400 bg-indigo-500/10 px-3 py-1.5 rounded-lg border border-indigo-500/20' 
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <BarChart3 size={18} />
          <span>Dashboard</span>
        </Link>

        <Link
          to="/upload"
          className={`flex items-center gap-2 text-sm font-medium transition-all ${
            isActive('/upload') 
              ? 'text-indigo-400 bg-indigo-500/10 px-3 py-1.5 rounded-lg border border-indigo-500/20' 
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <UploadCloud size={18} />
          <span>Study Materials</span>
        </Link>

        <div className="h-6 w-px bg-slate-800"></div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-800/40 border border-slate-700/50 px-3 py-1.5 rounded-lg">
            <div className="h-6 w-6 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold uppercase text-white">
              {user.username ? user.username.slice(0, 2) : 'US'}
            </div>
            <span className="text-sm font-semibold text-slate-200">{user.username}</span>
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-rose-400 bg-rose-500/5 border border-rose-500/10 hover:border-rose-500/30 hover:bg-rose-500/10 px-3 py-1.5 rounded-lg transition-all"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
