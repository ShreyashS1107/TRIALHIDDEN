'use client';

import React, { useState } from 'react';
import { Cpu, Send, Sparkles, MessageSquare, Bot, User, ArrowUpRight, X } from 'lucide-react';
import { queryPaimanaAssistant, AssistantMessage } from '@/lib/api/assistant';

interface Section16Props {
  isOpen?: boolean;
  onClose?: () => void;
  isFloating?: boolean;
}

export default function Section16_AIAssistant({ isOpen = true, onClose, isFloating = false }: Section16Props) {
  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'PAIMANA Intelligence ready. Operating over 21,555 longitudinal project snapshots with Platt-calibrated delay models and deterministic Execution Stress (ESI) surveillance. How can I assist your review?',
      timestamp: '21:30',
      dataPoints: [
        { label: 'Active Projects', value: '2,741 tracked' },
        { label: 'Time-Series', value: '15 months' },
        { label: 'Model Metrics', value: 'OOT ROC 0.9723 / 0.9895' },
      ],
      suggestedFollowUps: [
        'Which projects need immediate attention?',
        'Why is project 400178 at risk?',
        'Show projects with large cost revisions',
      ],
    },
  ]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const suggestedPrompts = [
    'Which projects need immediate attention?',
    'Why is project 400178 at risk?',
    'Show projects with large cost revisions',
    'What changed in this project over the last six months?',
  ];

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input.trim();
    if (!textToSend || loading) return;

    const userMsg: AssistantMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const resp = await queryPaimanaAssistant(textToSend);
      setMessages((prev) => [...prev, resp]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          text: 'Encountered telemetry error processing prompt against local project schema.',
          timestamp: 'Now',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const content = (
    <div className="flex flex-col h-[520px] glass-panel rounded-2xl border-cyan-500/30 overflow-hidden shadow-2xl bg-navy-950">
      {/* Assistant Header */}
      <div className="p-4 bg-navy-900 border-b border-cyan-500/20 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center">
            <Cpu className="w-4 h-4 text-cyan" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white font-mono flex items-center gap-2">
              <span>PAIMANA INTELLIGENCE</span>
              <span className="w-2 h-2 rounded-full bg-cyan animate-pulse" />
            </h4>
            <span className="text-[10px] text-concrete-400 font-mono">
              MoSPI / IPMD Project Surveillance Assistant
            </span>
          </div>
        </div>

        {isFloating && onClose && (
          <button onClick={onClose} className="p-1 rounded-lg text-concrete-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 no-scrollbar">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                m.sender === 'user'
                  ? 'bg-cyan-500/20 text-white border border-cyan-500/40 rounded-br-none'
                  : 'bg-navy-900/90 text-concrete-200 border border-concrete-800 rounded-bl-none'
              }`}
            >
              <div className="whitespace-pre-line font-sans">{m.text}</div>

              {/* Data Points Grid if returned */}
              {m.dataPoints && m.dataPoints.length > 0 && (
                <div className="mt-3 pt-2 border-t border-concrete-800 space-y-1 font-mono text-[11px]">
                  {m.dataPoints.map((dp, idx) => (
                    <div key={idx} className="flex items-start justify-between gap-2">
                      <span className="text-cyan font-semibold">{dp.label}:</span>
                      <span className="text-white text-right">{dp.value}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <span className="text-[9px] font-mono text-concrete-500 mt-1 px-1">
              {m.timestamp}
            </span>

            {/* Suggested Followups */}
            {m.suggestedFollowUps && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {m.suggestedFollowUps.map((fu, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(fu)}
                    className="text-[10px] font-mono px-2 py-1 rounded bg-navy-900 hover:bg-navy-850 text-cyan-300 border border-cyan-500/30 transition-colors"
                  >
                    ↳ {fu}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-xs font-mono text-cyan animate-pulse p-2">
            <Cpu className="w-3.5 h-3.5 animate-spin" />
            <span>Consulting longitudinal inference models...</span>
          </div>
        )}
      </div>

      {/* Suggested Prompts Pill Bar */}
      <div className="px-4 py-2 bg-navy-900/50 border-t border-concrete-800 flex items-center gap-2 overflow-x-auto no-scrollbar text-[11px] font-mono">
        <span className="text-concrete-500 uppercase text-[9px] flex-shrink-0">PROMPTS:</span>
        {suggestedPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            className="px-2.5 py-1 rounded bg-navy-950 hover:bg-navy-850 text-concrete-300 hover:text-cyan border border-concrete-800 whitespace-nowrap transition-colors"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <div className="p-3 bg-navy-900 border-t border-cyan-500/20 flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about high-risk projects, cost revisions, or ESI indicators..."
          className="flex-1 bg-navy-950 border border-concrete-800 text-white placeholder:text-concrete-500 px-3 py-2 rounded-xl text-xs font-sans outline-none focus:border-cyan"
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          className="p-2.5 rounded-xl bg-cyan hover:bg-cyan-300 text-navy-950 font-bold transition-all disabled:opacity-40"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );

  if (isFloating) {
    if (!isOpen) return null;
    return (
      <div className="fixed bottom-6 right-6 z-50 w-96 max-w-[90vw] animate-fade-in shadow-2xl">
        {content}
      </div>
    );
  }

  return (
    <section id="assistant" className="relative w-full py-24 bg-navy-900 border-t border-cyan-500/20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-3">
            <Cpu className="w-3.5 h-3.5" />
            <span>SECTION 16 • CONTEXTUAL PROJECT ASSISTANT</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-2">
            PAIMANA INTELLIGENCE
          </h2>
          <p className="text-xs sm:text-sm text-concrete-300">
            A specialized decision assistant grounded directly in the 21,555 longitudinal project dataset. Not a generic chatbot.
          </p>
        </div>

        {content}
      </div>
    </section>
  );
}
