import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { ArrowLeft, ArrowRight, CheckCircle, XCircle, BookOpen, AlertTriangle, Loader, HelpCircle } from 'lucide-react';

const Quiz = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Quiz Taking state
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({}); // { questionId: selectedOptionIndex }
  const [submitting, setSubmitting] = useState(false);

  // Result state
  const [result, setResult] = useState(null);

  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        const res = await api.get(`/quizzes/${id}`);
        setQuiz(res.data);
      } catch (err) {
        console.error("Quiz fetch error:", err);
        setError("Failed to fetch quiz details.");
      } finally {
        setLoading(false);
      }
    };
    fetchQuiz();
  }, [id]);

  const handleSelectOption = (qId, optionIdx) => {
    if (result) return;
    setAnswers(prev => ({
      ...prev,
      [qId]: optionIdx
    }));
  };

  const handleSubmit = async () => {
    if (Object.keys(answers).length < quiz.questions.length) {
      if (!window.confirm("You have unanswered questions. Are you sure you want to submit?")) {
        return;
      }
    }

    setSubmitting(true);
    setError('');

    const payload = quiz.questions.map(q => {
      const ans = answers[q.id];
      const isText = q.type === 'fill_in_the_blank' || q.type === 'short_answer' || q.type === 'coding';
      let textVal = null;
      if (isText) {
        textVal = ans !== undefined ? ans : (q.code_template || '');
      }
      return {
        question_id: q.id,
        selected_option: (!isText && typeof ans === 'number') ? ans : -1,
        text_response: textVal
      };
    });

    try {
      const res = await api.post(`/quizzes/submit/${id}`, payload);
      setResult(res.data);
    } catch (err) {
      console.error("Submit error:", err);
      setError("Failed to evaluate quiz answers.");
    } finally {
      setSubmitting(false);
    }
  };


  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-100px)] items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  if (error || !quiz) {
    return (
      <div className="max-w-md mx-auto mt-20 p-6 bg-[#0e1626]/60 border border-slate-800 rounded-2xl text-center">
        <HelpCircle size={48} className="text-rose-500 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-slate-200">Error loading quiz</h3>
        <p className="text-slate-500 text-sm mt-1">{error || "Quiz not found."}</p>
        <button onClick={() => navigate('/upload')} className="mt-6 px-4 py-2 bg-slate-800 text-white rounded-xl text-sm font-semibold hover:bg-slate-700">
          Go Back
        </button>
      </div>
    );
  }

  const questions = quiz.questions;
  const currentQuestion = questions[currentIdx];

  // Result View
  if (result) {
    const accuracy = Math.round((result.score / result.total_questions) * 100);
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 animate-fade-in">
        <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-8 backdrop-blur-md mb-8 relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-2xl">
          <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-bl-full pointer-events-none"></div>
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-black text-2xl text-white shadow-lg">
              {result.score}/{result.total_questions}
            </div>
            <div>
              <h2 className="text-2xl font-black text-white">Quiz Evaluation Completed</h2>
              <p className="text-sm text-slate-400 mt-1">Accuracy: <span className="font-bold text-indigo-400">{accuracy}%</span></p>
            </div>
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700/50 text-white font-bold transition-all text-sm shadow-md"
          >
            Return to Dashboard
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <h3 className="text-xl font-bold text-slate-200 mb-2">Question Breakdown</h3>
            {result.evaluated_questions.map((q, idx) => {
              const originalQ = quiz.questions.find(orig => orig.id === q.question_id);
              return (
                <div key={q.question_id} className={`p-6 border rounded-2xl bg-[#0e1626]/40 backdrop-blur-sm ${q.is_correct ? 'border-emerald-500/20' : 'border-rose-500/20'}`}>
                  <div className="flex items-start justify-between gap-3">
                    <h4 className="text-sm font-bold text-slate-200">Q{idx + 1}. {q.question_text}</h4>
                    {q.is_correct ? (
                      <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 shrink-0">
                        <CheckCircle size={12} />
                        Correct
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[11px] font-bold text-rose-400 bg-rose-500/10 px-2.5 py-0.5 rounded-full border border-rose-500/20 shrink-0">
                        <XCircle size={12} />
                        Incorrect
                      </span>
                    )}
                  </div>

                  <div className="mt-4 space-y-3">
                    {/* Render MCQs and True/False option lists */}
                    {(originalQ && (originalQ.type === "mcq" || originalQ.type === "true_false")) && originalQ.options && originalQ.options.map((option, optIdx) => {
                      let optionStyle = "border-slate-800 bg-slate-900/10 text-slate-400";
                      if (optIdx === q.correct_option) {
                        optionStyle = "border-emerald-500/30 bg-emerald-500/5 text-emerald-300 font-semibold";
                      } else if (optIdx === q.selected_option && !q.is_correct) {
                        optionStyle = "border-rose-500/30 bg-rose-500/5 text-rose-300 font-semibold";
                      }
                      
                      return (
                        <div key={optIdx} className={`px-4 py-3 border rounded-xl text-xs flex items-center justify-between ${optionStyle}`}>
                          <span>{option}</span>
                          {optIdx === q.correct_option && <span className="text-[10px] uppercase font-bold text-emerald-400">Correct Answer</span>}
                          {optIdx === q.selected_option && !q.is_correct && <span className="text-[10px] uppercase font-bold text-rose-400">Your Selection</span>}
                        </div>
                      );
                    })}

                    {/* Render Text responses (Fill in Blank, Short Answer, Coding) */}
                    {(originalQ && (originalQ.type === "fill_in_the_blank" || originalQ.type === "short_answer" || originalQ.type === "coding")) && (
                      <div className="space-y-3">
                        <div className="p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl text-xs">
                          <span className="text-[10px] font-bold text-slate-500 block mb-1">YOUR RESPONSE:</span>
                          <span className="text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">{q.text_response || "(No answer provided)"}</span>
                        </div>
                        <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-xl text-xs">
                          <span className="text-[10px] font-bold text-emerald-400 block mb-1">REFERENCE CORRECT ANSWER:</span>
                          <span className="text-emerald-300 leading-relaxed font-mono whitespace-pre-wrap">
                            {originalQ.correct_answer || "Reference criteria"}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>


                  <div className="mt-4 p-4 bg-indigo-500/5 border border-indigo-500/10 rounded-xl">
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block mb-1">AI Agent Explanation</span>
                    <p className="text-xs text-slate-300 leading-relaxed">{q.explanation}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="lg:col-span-1 space-y-6">
            <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-lg">
              <h3 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
                <AlertTriangle size={18} className="text-amber-500" />
                <span>Identified Weak Topics</span>
              </h3>
              {result.weak_topics.length === 0 ? (
                <div className="text-center py-4 text-emerald-400 text-xs font-semibold">
                  No weak topics! Outstanding execution.
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {result.weak_topics.map((t, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-semibold">
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {result.strong_topics && result.strong_topics.length > 0 && (
              <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-lg">
                <h3 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
                  <CheckCircle size={18} className="text-emerald-400" />
                  <span>Identified Strong Topics</span>
                </h3>
                <div className="flex flex-wrap gap-2">
                  {result.strong_topics.map((t, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-lg relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-purple-500/5 to-transparent rounded-bl-full pointer-events-none"></div>
              <h3 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
                <BookOpen size={18} className="text-purple-400" />
                <span>AI Agent Study Plan</span>
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                {result.study_plan || "No custom plan generated."}
              </p>
            </div>

            {result.progress_summary && (
              <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-lg relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-emerald-500/5 to-transparent rounded-bl-full pointer-events-none"></div>
                <h3 className="text-lg font-bold text-slate-200 mb-4 flex items-center gap-2">
                  <CheckCircle size={18} className="text-emerald-400" />
                  <span>AI Progress Tracker</span>
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                  {result.progress_summary}
                </p>
              </div>
            )}

          </div>
        </div>
      </div>
    );
  }

  const progressPercent = Math.round(((currentIdx + 1) / questions.length) * 100);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 animate-fade-in">
      <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md mb-6 shadow-xl flex items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-indigo-400 tracking-wide uppercase">Active Exam Prep</span>
          <h2 className="text-xl font-extrabold text-white mt-0.5">{quiz.title}</h2>
        </div>
        <div className="text-right shrink-0">
          <span className="text-sm font-bold text-slate-300">Question {currentIdx + 1} of {questions.length}</span>
          <div className="w-24 bg-slate-900 border border-slate-800 rounded-full h-2 mt-1.5 overflow-hidden">
            <div className="bg-indigo-500 h-full transition-all duration-300" style={{ width: `${progressPercent}%` }}></div>
          </div>
        </div>
      </div>

      <div className="bg-[#0e1626]/60 border border-slate-800 rounded-2xl p-8 backdrop-blur-md shadow-xl mb-6 relative overflow-hidden min-h-[300px] flex flex-col justify-between">
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-indigo-500/5 rounded-full blur-3xl"></div>
        
        <div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-widest block mb-2">Question {currentIdx + 1}</span>
          <h3 className="text-lg font-bold text-white leading-relaxed mb-6">
            {currentQuestion.question_text}
          </h3>

          <div className="space-y-3">
            {/* MCQ (multiple choice) */}
            {currentQuestion.type === "mcq" && currentQuestion.options && currentQuestion.options.map((option, idx) => {
              const isSelected = answers[currentQuestion.id] === idx;
              return (
                <button
                  key={idx}
                  onClick={() => handleSelectOption(currentQuestion.id, idx)}
                  className={`w-full text-left px-5 py-4 border rounded-xl text-sm font-medium transition-all flex items-center justify-between group ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-500/10 text-white font-semibold shadow-md shadow-indigo-500/5'
                      : 'border-slate-800 hover:border-slate-700 bg-slate-900/30 text-slate-300'
                  }`}
                >
                  <span>{option}</span>
                  <div className={`h-5 w-5 rounded-full border flex items-center justify-center shrink-0 ${
                    isSelected ? 'border-indigo-500 bg-indigo-500 text-white' : 'border-slate-700 group-hover:border-slate-500'
                  }`}>
                    {isSelected && <div className="h-1.5 w-1.5 rounded-full bg-white"></div>}
                  </div>
                </button>
              );
            })}

            {/* True/False */}
            {currentQuestion.type === "true_false" && ["True", "False"].map((option, idx) => {
              const isSelected = answers[currentQuestion.id] === idx;
              return (
                <button
                  key={idx}
                  onClick={() => handleSelectOption(currentQuestion.id, idx)}
                  className={`w-full text-left px-5 py-4 border rounded-xl text-sm font-medium transition-all flex items-center justify-between group ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-500/10 text-white font-semibold shadow-md shadow-indigo-500/5'
                      : 'border-slate-800 hover:border-slate-700 bg-slate-900/30 text-slate-300'
                  }`}
                >
                  <span>{option}</span>
                  <div className={`h-5 w-5 rounded-full border flex items-center justify-center shrink-0 ${
                    isSelected ? 'border-indigo-500 bg-indigo-500 text-white' : 'border-slate-700 group-hover:border-slate-500'
                  }`}>
                    {isSelected && <div className="h-1.5 w-1.5 rounded-full bg-white"></div>}
                  </div>
                </button>
              );
            })}

            {/* Fill in the Blanks */}
            {currentQuestion.type === "fill_in_the_blank" && (
              <div className="space-y-2">
                <input
                  type="text"
                  placeholder="Type your answer here..."
                  value={answers[currentQuestion.id] || ""}
                  onChange={(e) => setAnswers(prev => ({ ...prev, [currentQuestion.id]: e.target.value }))}
                  className="w-full px-5 py-4 bg-slate-950/60 border border-slate-850 hover:border-slate-750 focus:border-indigo-500 rounded-xl text-sm text-slate-205 focus:outline-none transition-all placeholder:text-slate-600 font-medium"
                />
              </div>
            )}

            {/* Short Answer */}
            {currentQuestion.type === "short_answer" && (
              <div className="space-y-2">
                <textarea
                  rows={4}
                  placeholder="Explain your answer in a few sentences..."
                  value={answers[currentQuestion.id] || ""}
                  onChange={(e) => setAnswers(prev => ({ ...prev, [currentQuestion.id]: e.target.value }))}
                  className="w-full px-5 py-4 bg-slate-955/60 border border-slate-855 hover:border-slate-755 focus:border-indigo-500 rounded-xl text-sm text-slate-205 focus:outline-none transition-all placeholder:text-slate-600 resize-none font-medium leading-relaxed"
                />
              </div>
            )}

            {/* Coding Challenge */}
            {currentQuestion.type === "coding" && (
              <div className="space-y-3">
                <span className="text-xs text-slate-500 block mb-1">Code Workspace:</span>
                <textarea
                  rows={8}
                  placeholder="// Write your code solution here"
                  value={answers[currentQuestion.id] !== undefined ? answers[currentQuestion.id] : (currentQuestion.code_template || "")}
                  onChange={(e) => setAnswers(prev => ({ ...prev, [currentQuestion.id]: e.target.value }))}
                  className="w-full px-5 py-4 bg-black/50 border border-slate-855 focus:border-indigo-500 rounded-xl text-xs text-emerald-400 font-mono focus:outline-none transition-all resize-none leading-relaxed"
                />
              </div>
            )}
          </div>

        </div>

        <div className="mt-8 pt-6 border-t border-slate-900/60 flex items-center justify-between gap-4">
          <button
            onClick={() => setCurrentIdx(prev => Math.max(0, prev - 1))}
            disabled={currentIdx === 0}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white font-semibold transition-all text-xs disabled:opacity-40 disabled:pointer-events-none"
          >
            <ArrowLeft size={14} />
            <span>Previous</span>
          </button>

          {currentIdx === questions.length - 1 ? (
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-bold transition-all text-xs shadow-md shadow-indigo-500/20 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader size={14} className="animate-spin" />
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <span>Submit Exam</span>
                  <CheckCircle size={14} />
                </>
              )}
            </button>
          ) : (
            <button
              onClick={() => setCurrentIdx(prev => Math.min(questions.length - 1, prev + 1))}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all text-xs"
            >
              <span>Next</span>
              <ArrowRight size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Quiz;
