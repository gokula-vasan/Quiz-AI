import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { UploadCloud, FileText, Play, Trash2, Loader, CheckCircle } from 'lucide-react';

const Upload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState({});
  const [documents, setDocuments] = useState([]);
  const [quizzes, setQuizzes] = useState([]);
  const [error, setError] = useState('');
  const [preferences, setPreferences] = useState({});
  const navigate = useNavigate();

  const fetchDocumentsAndQuizzes = async () => {
    try {
      const [docsRes, quizzesRes] = await Promise.all([
        api.get('/documents'),
        api.get('/quizzes')
      ]);
      setDocuments(docsRes.data);
      setQuizzes(quizzesRes.data);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError("Failed to load documents or quizzes.");
    }
  };

  useEffect(() => {
    fetchDocumentsAndQuizzes();
  }, []);

  const handleFileChange = (e) => {
    setError('');
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const ext = selectedFile.name.split('.').pop().toLowerCase();
      if (ext !== 'pdf' && ext !== 'pptx' && ext !== 'docx' && ext !== 'txt') {
        setError('Only PDF, PPTX, DOCX, and TXT files are supported.');
        setFile(null);
      } else {
        setFile(selectedFile);
      }
    }
  };



  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setFile(null);
      await fetchDocumentsAndQuizzes();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  const handleGenerateQuiz = async (docId) => {
    setGenerating(prev => ({ ...prev, [docId]: true }));
    setError('');
    const pref = preferences[docId] || { difficulty: 'Medium', question_count: 10, quiz_mode: 'theory', selected_topic: '' };
    try {
      const res = await api.post(`/quizzes/generate/${docId}`, {
        difficulty: pref.difficulty || 'Medium',
        question_count: pref.question_count || 10,
        quiz_mode: pref.quiz_mode || 'theory',
        selected_topic: pref.selected_topic || undefined
      });
      await fetchDocumentsAndQuizzes();
      navigate(`/quiz/${res.data.id}`);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to generate quiz.');
    } finally {
      setGenerating(prev => ({ ...prev, [docId]: false }));
    }
  };



  const handleDeleteDoc = async (docId) => {
    if (!window.confirm("Are you sure you want to delete this document and its associated quizzes?")) return;
    try {
      await api.delete(`/documents/${docId}`);
      await fetchDocumentsAndQuizzes();
    } catch (err) {
      console.error(err);
      setError("Failed to delete document.");
    }
  };

  const getQuizForDoc = (docId) => {
    return quizzes.find(q => q.document_id === docId);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-white">Study Materials</h1>
        <p className="text-slate-400 mt-1">Upload your documents to analyze and generate autonomous quizzes</p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md sticky top-28">
            <h2 className="text-xl font-bold text-slate-200 mb-4">Upload Study Material</h2>
            
            <form onSubmit={handleUpload} className="space-y-4">
              <label className="border-2 border-dashed border-slate-800 hover:border-indigo-500/50 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-all bg-slate-900/20 hover:bg-slate-900/40">
                <input
                  type="file"
                  accept=".pdf,.pptx,.docx,.txt"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <UploadCloud size={40} className="text-slate-500 mb-3" />
                <span className="text-sm font-semibold text-slate-300 text-center">
                  {file ? file.name : "Select PDF, PPTX, DOCX, or TXT study material"}
                </span>


                <span className="text-xs text-slate-500 mt-1">Maximum size 10MB</span>
              </label>

              {file && (
                <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800 flex items-center gap-3">
                  <FileText size={18} className="text-indigo-400" />
                  <div className="overflow-hidden">
                    <p className="text-xs font-semibold text-slate-300 truncate">{file.name}</p>
                    <p className="text-[10px] text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={!file || uploading}
                className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all shadow-md shadow-indigo-600/10 flex items-center justify-center gap-2 disabled:opacity-40 disabled:pointer-events-none"
              >
                {uploading ? (
                  <>
                    <Loader size={16} className="animate-spin" />
                    <span>Processing PDF...</span>
                  </>
                ) : (
                  <span>Upload & Analyze</span>
                )}
              </button>
            </form>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-bold text-slate-200 mb-2">My Documents</h2>

          {documents.length === 0 ? (
            <div className="bg-[#0e1626]/30 border border-slate-800/80 rounded-2xl p-12 text-center">
              <FileText size={48} className="text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-bold text-slate-300">No documents yet</h3>
              <p className="text-slate-500 text-sm mt-1">Upload a PDF study material to get started</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {documents.map((doc) => {
                const associatedQuiz = getQuizForDoc(doc.id);
                const isGenerating = generating[doc.id];
                return (
                  <div key={doc.id} className="bg-[#0e1626]/60 border border-slate-800 hover:border-slate-700 p-5 rounded-2xl transition-all flex flex-col justify-between min-h-[210px] h-auto relative overflow-hidden group shadow-lg">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-indigo-500/5 to-transparent rounded-bl-full pointer-events-none"></div>
                    <div>
                      <div className="flex justify-between items-start gap-2">
                        <div className="p-2 bg-slate-900/80 rounded-lg text-indigo-400 border border-slate-800 shrink-0">
                          <FileText size={20} />
                        </div>
                        <button
                          onClick={() => handleDeleteDoc(doc.id)}
                          className="text-slate-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-500/5 border border-transparent hover:border-rose-500/10 transition-all"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>

                      <h3 className="text-sm font-bold text-slate-200 mt-3 truncate group-hover:text-indigo-300 transition-colors">
                        {doc.filename}
                      </h3>
                      <p className="text-[11px] text-slate-500 mt-1">
                        Uploaded: {new Date(doc.uploaded_at).toLocaleDateString()}
                      </p>

                      {!associatedQuiz && (
                        <div className="flex items-center gap-3 mt-3">
                          <div className="flex flex-col gap-0.5">
                            <span className="text-[9px] text-slate-500 uppercase font-black tracking-wider">Difficulty</span>
                            <select
                              value={preferences[doc.id]?.difficulty || "Medium"}
                              onChange={(e) => setPreferences(prev => ({
                                ...prev,
                                [doc.id]: { ...(prev[doc.id] || { question_count: 10, quiz_mode: "theory" }), difficulty: e.target.value }
                              }))}
                              className="bg-[#0b101d] border border-slate-850 rounded-lg px-2 py-1 text-[10px] font-bold text-indigo-400 focus:outline-none focus:border-indigo-500/55 cursor-pointer"
                            >
                              <option value="Easy">Easy</option>
                              <option value="Medium">Medium</option>
                              <option value="Hard">Hard</option>
                            </select>
                          </div>
                          
                          <div className="flex flex-col gap-0.5">
                            <span className="text-[9px] text-slate-500 uppercase font-black tracking-wider">Questions</span>
                            <select
                              value={preferences[doc.id]?.question_count || 10}
                              onChange={(e) => setPreferences(prev => ({
                                ...prev,
                                [doc.id]: { ...(prev[doc.id] || { difficulty: "Medium", quiz_mode: "theory" }), question_count: parseInt(e.target.value) }
                              }))}
                              className="bg-[#0b101d] border border-slate-850 rounded-lg px-2 py-1 text-[10px] font-bold text-indigo-400 focus:outline-none focus:border-indigo-500/55 cursor-pointer"
                            >
                              <option value={5}>5 Qs</option>
                              <option value={10}>10 Qs</option>
                              <option value={15}>15 Qs</option>
                              <option value={20}>20 Qs</option>
                            </select>
                          </div>

                          <div className="flex flex-col gap-0.5">
                            <span className="text-[9px] text-slate-500 uppercase font-black tracking-wider">Format</span>
                            <select
                              value={preferences[doc.id]?.quiz_mode || "theory"}
                              onChange={(e) => setPreferences(prev => ({
                                ...prev,
                                [doc.id]: { ...(prev[doc.id] || { difficulty: "Medium", question_count: 10 }), quiz_mode: e.target.value }
                              }))}
                              className="bg-[#0b101d] border border-slate-850 rounded-lg px-2 py-1 text-[10px] font-bold text-indigo-400 focus:outline-none focus:border-indigo-500/55 cursor-pointer"
                            >
                              <option value="theory">Theory Only</option>
                              <option value="coding">Coding Only</option>
                              <option value="mixed">Mixed Mode</option>
                            </select>
                          </div>

                          {doc.concepts && doc.concepts.length > 0 && (
                            <div className="flex flex-col gap-0.5">
                              <span className="text-[9px] text-slate-500 uppercase font-black tracking-wider">Practice Topic</span>
                              <select
                                value={preferences[doc.id]?.selected_topic || ""}
                                onChange={(e) => setPreferences(prev => ({
                                  ...prev,
                                  [doc.id]: { ...(prev[doc.id] || { difficulty: "Medium", question_count: 10, quiz_mode: "theory" }), selected_topic: e.target.value }
                                }))}
                                className="bg-[#0b101d] border border-slate-850 rounded-lg px-2 py-1 text-[10px] font-bold text-indigo-400 focus:outline-none focus:border-indigo-500/55 cursor-pointer max-w-[125px] truncate"
                              >
                                <option value="">All Topics</option>
                                {Array.from(new Set(doc.concepts.map(c => c.topic))).map((topicName, idx) => (
                                  <option key={idx} value={topicName}>{topicName}</option>
                                ))}
                              </select>
                            </div>
                          )}
                        </div>
                      )}

                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-900/60 flex items-center justify-between">

                      {associatedQuiz ? (
                        <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-semibold">
                          <CheckCircle size={14} />
                          <span>Quiz Ready</span>
                        </div>
                      ) : (
                        <span className="text-[11px] text-slate-500">No quiz generated</span>
                      )}

                      {associatedQuiz ? (
                        <button
                          onClick={() => navigate(`/quiz/${associatedQuiz.id}`)}
                          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 hover:bg-indigo-600 hover:text-white text-xs font-bold transition-all"
                        >
                          <Play size={12} />
                          <span>Start Quiz</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => handleGenerateQuiz(doc.id)}
                          disabled={isGenerating}
                          className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white text-xs font-bold transition-all disabled:opacity-55"
                        >
                          {isGenerating ? (
                            <>
                              <Loader size={12} className="animate-spin" />
                              <span>Generating...</span>
                            </>
                          ) : (
                            <>
                              <Play size={12} />
                              <span>Generate Quiz</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Upload;
