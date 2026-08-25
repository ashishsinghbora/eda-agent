import React from 'react';
import { 
  GitFork, 
  GitPullRequest, 
  CheckCircle2, 
  Clock, 
  Sparkles, 
  Cpu, 
  Terminal, 
  Layers, 
  ArrowRight,
  ExternalLink,
  ShieldAlert
} from 'lucide-react';
import { backendAdapterGuide, goodFirstIssues, roadmapMilestones } from '../data/contributorData';
import { CodeBlock } from './CodeBlock';

export const ContributorRoadmapSection: React.FC = () => {
  return (
    <section id="roadmap" className="py-20 bg-[#0B111D] border-t border-[#20304C] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#10192A] border border-purple-500/30 text-purple-300 text-xs font-mono mb-3">
            <GitFork className="w-3.5 h-3.5 text-purple-400" />
            <span>Community & Development Roadmap</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
            Contributor Hub & 2025–2026 Roadmap
          </h2>
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            Help shape the future of autonomous hardware verification. Add support for commercial EDA simulators, ASIC backend flows, and formal model checking.
          </p>
        </div>

        {/* SECTION 1: HOW TO ADD A NEW EDA BACKEND */}
        <div className="rounded-2xl border border-[#20304C] bg-[#070B12] overflow-hidden shadow-2xl p-6 mb-16">
          <div className="flex items-center space-x-2 text-sm font-bold text-slate-100 font-mono mb-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <span>Architectural Deep Dive: Adding Custom EDA Tool Adapters</span>
          </div>
          <p className="text-xs text-slate-400 mb-4 leading-relaxed font-sans">
            {backendAdapterGuide.overview}
          </p>

          <CodeBlock
            code={backendAdapterGuide.snippet}
            language="python"
            filename="eda_agent/runners/vivado_runner.py"
            maxHeight="320px"
          />
        </div>

        {/* SECTION 2: GOOD FIRST ISSUES */}
        <div className="mb-16">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold font-mono text-slate-100 flex items-center space-x-2">
                <GitPullRequest className="w-5 h-5 text-purple-400" />
                <span>Good First Issues & PR Opportunities</span>
              </h3>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                Ready to contribute? Pick an issue below and submit a pull request!
              </p>
            </div>
            <a
              href="https://github.com/ashishsinghbora/eda-agent/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:flex items-center space-x-1 text-xs font-mono text-cyan-400 hover:underline"
            >
              <span>View all issues</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {goodFirstIssues.map((issue) => (
              <div
                key={issue.id}
                className="p-5 rounded-xl bg-[#070B12] border border-[#20304C] hover:border-purple-500/50 transition space-y-3 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono font-bold text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                      {issue.id}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold ${
                        issue.difficulty === 'Easy'
                          ? 'text-emerald-400'
                          : issue.difficulty === 'Intermediate'
                          ? 'text-amber-400'
                          : 'text-rose-400'
                      }`}
                    >
                      {issue.difficulty}
                    </span>
                  </div>

                  <h4 className="font-bold text-xs text-slate-100 font-sans">
                    {issue.title}
                  </h4>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                    {issue.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-[#16233B] flex flex-wrap gap-1">
                  {issue.tags.map((tag) => (
                    <span key={tag} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#10192A] text-slate-400 border border-[#20304C]">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION 3: 2025-2026 INTERACTIVE ROADMAP TIMELINE */}
        <div className="rounded-2xl border border-[#20304C] bg-[#070B12] p-8 shadow-2xl">
          <h3 className="text-xl font-bold font-mono text-slate-100 mb-8 text-center flex items-center justify-center space-x-2">
            <Clock className="w-5 h-5 text-cyan-400" />
            <span>2025–2026 Project Roadmap</span>
          </h3>

          <div className="relative border-l-2 border-[#20304C] ml-4 md:ml-32 space-y-10">
            {roadmapMilestones.map((m, idx) => {
              const isCompleted = m.status === 'Completed';
              const isInProgress = m.status === 'In Progress';

              return (
                <div key={idx} className="relative pl-8">
                  
                  {/* Timeline node icon */}
                  <div
                    className={`absolute -left-[17px] top-1.5 w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                      isCompleted
                        ? 'bg-emerald-950 border-emerald-400 text-emerald-400'
                        : isInProgress
                        ? 'bg-amber-950 border-amber-400 text-amber-400 animate-pulse'
                        : 'bg-[#10192A] border-[#20304C] text-slate-500'
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4" />
                    ) : (
                      <Clock className="w-4 h-4" />
                    )}
                  </div>

                  {/* Quarter & Status Badge */}
                  <div className="flex items-center space-x-3 mb-1">
                    <span className="font-mono text-sm font-bold text-cyan-300">
                      {m.quarter}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                        isCompleted
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : isInProgress
                          ? 'bg-amber-950 text-amber-400 border border-amber-800'
                          : 'bg-[#10192A] text-slate-400 border border-[#20304C]'
                      }`}
                    >
                      {m.status.toUpperCase()}
                    </span>
                  </div>

                  {/* Title */}
                  <h4 className="text-base font-bold text-slate-100 font-sans mb-2">
                    {m.title}
                  </h4>

                  {/* Details List */}
                  <ul className="space-y-1.5 text-xs text-slate-400 font-sans">
                    {m.details.map((item, dIdx) => (
                      <li key={dIdx} className="flex items-start space-x-2">
                        <span className="text-cyan-400 mt-0.5">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>

                </div>
              );
            })}
          </div>
        </div>

      </div>
    </section>
  );
};
