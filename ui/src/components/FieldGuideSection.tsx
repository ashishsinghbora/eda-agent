import React, { useState } from 'react';
import { 
  BookOpen, 
  Code2, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Wrench, 
  Clock, 
  Cpu, 
  GitCompare, 
  Sparkles,
  ArrowRight,
  Terminal,
  Activity
} from 'lucide-react';
import { CodeBlock } from './CodeBlock';
import { uvmVsCocotbComparison, comparisonMetrics, fieldCaseStudies } from '../data/fieldGuideData';
import { CaseStudy } from '../types';

export const FieldGuideSection: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'comparison' | 'case-studies'>('comparison');
  const [selectedCaseId, setSelectedCaseId] = useState<string>('fsm_trap');
  const [caseViewMode, setCaseViewMode] = useState<'diff' | 'diagnostic' | 'testbench'>('diff');

  const selectedCase: CaseStudy = fieldCaseStudies.find((c) => c.id === selectedCaseId) || fieldCaseStudies[0];

  return (
    <section id="field-guide" className="py-20 bg-[#0B111D] border-t border-[#20304C] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#10192A] border border-purple-500/30 text-purple-300 text-xs font-mono mb-3">
            <BookOpen className="w-3.5 h-3.5 text-purple-400" />
            <span>VLSI Engineer's Field Guide</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
            Why & How to Use EDA-Agent
          </h2>
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            Eliminate tedious UVM macro boilerplate and debug insidious hardware bugs (FSM traps, transparent latches, CDC metastabilities, timing slack) with autonomous self-repair.
          </p>

          {/* Sub-navigation tabs */}
          <div className="flex justify-center mt-6">
            <div className="inline-flex p-1 rounded-xl bg-[#070B12] border border-[#20304C]">
              <button
                onClick={() => setActiveTab('comparison')}
                className={`flex items-center space-x-2 px-5 py-2 rounded-lg text-xs font-mono transition ${
                  activeTab === 'comparison'
                    ? 'bg-gradient-to-r from-cyan-950 to-purple-950 text-cyan-300 border border-cyan-500/40 shadow-sm font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <GitCompare className="w-3.5 h-3.5" />
                <span>UVM vs EDA-Agent (cocotb)</span>
              </button>
              <button
                onClick={() => setActiveTab('case-studies')}
                className={`flex items-center space-x-2 px-5 py-2 rounded-lg text-xs font-mono transition ${
                  activeTab === 'case-studies'
                    ? 'bg-gradient-to-r from-purple-950 to-cyan-950 text-purple-300 border border-purple-500/40 shadow-sm font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Real-World Hardware Failure Case Studies</span>
              </button>
            </div>
          </div>
        </div>

        {/* TAB 1: UVM VS COCOTB COMPARISON */}
        {activeTab === 'comparison' && (
          <div className="space-y-12">
            
            {/* Side-by-Side Code Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Left: Traditional UVM */}
              <div className="space-y-2">
                <div className="flex items-center justify-between px-2">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                    <span className="font-mono text-xs font-bold text-slate-300">
                      Traditional UVM 1.2 SystemVerilog
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-rose-400 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800">
                    150+ lines boilerplate
                  </span>
                </div>
                <CodeBlock
                  code={uvmVsCocotbComparison.uvmCode}
                  language="systemverilog"
                  filename="tb_alu_uvm_sequence.sv"
                  maxHeight="380px"
                />
              </div>

              {/* Right: EDA-Agent Cocotb */}
              <div className="space-y-2">
                <div className="flex items-center justify-between px-2">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span className="font-mono text-xs font-bold text-cyan-300">
                      EDA-Agent Autonomous Cocotb
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                    24 lines clean async Python
                  </span>
                </div>
                <CodeBlock
                  code={uvmVsCocotbComparison.cocotbCode}
                  language="python"
                  filename="test_alu_8bit.py"
                  maxHeight="380px"
                />
              </div>

            </div>

            {/* Comparison Matrix Table */}
            <div className="rounded-2xl border border-[#20304C] bg-[#070B12] overflow-hidden shadow-xl">
              <div className="px-6 py-4 bg-[#10192A] border-b border-[#20304C]">
                <h3 className="text-base font-bold text-slate-100 font-mono flex items-center space-x-2">
                  <GitCompare className="w-4 h-4 text-cyan-400" />
                  <span>Feature & Engineering Overhead Comparison</span>
                </h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-sans">
                  <thead className="bg-[#0B111D] border-b border-[#20304C] text-slate-400 font-mono uppercase text-[11px]">
                    <tr>
                      <th className="py-3.5 px-6">Evaluation Dimension</th>
                      <th className="py-3.5 px-6 text-rose-300">Traditional UVM / SV</th>
                      <th className="py-3.5 px-6 text-cyan-300">EDA-Agent + cocotb</th>
                      <th className="py-3.5 px-6 text-emerald-400">Key Advantage</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#16233B] font-mono">
                    {comparisonMetrics.map((m, idx) => (
                      <tr key={idx} className="hover:bg-[#10192A]/50 transition">
                        <td className="py-3.5 px-6 font-bold text-slate-200">{m.feature}</td>
                        <td className="py-3.5 px-6 text-slate-400 font-sans">{m.uvm}</td>
                        <td className="py-3.5 px-6 text-cyan-300 font-sans">{m.edaAgent}</td>
                        <td className="py-3.5 px-6 text-emerald-400 font-sans font-medium">{m.advantage}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

        {/* TAB 2: REAL-WORLD FAILURE CASE STUDIES */}
        {activeTab === 'case-studies' && (
          <div className="space-y-8">
            
            {/* Case Selector Pills */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {fieldCaseStudies.map((study) => {
                const isSelected = study.id === selectedCaseId;
                return (
                  <button
                    key={study.id}
                    onClick={() => setSelectedCaseId(study.id)}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      isSelected
                        ? 'bg-purple-950/40 border-purple-500/60 shadow-[0_0_15px_rgba(168,85,247,0.2)]'
                        : 'bg-[#070B12] border-[#20304C] hover:border-purple-500/40 text-slate-400'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#10192A] text-purple-400 border border-[#20304C]">
                        {study.category}
                      </span>
                      <span className={`text-[10px] font-mono font-bold ${study.severity === 'Critical' ? 'text-rose-400' : 'text-amber-400'}`}>
                        {study.severity}
                      </span>
                    </div>
                    <h4 className="font-bold text-xs text-slate-200 line-clamp-2">
                      {study.title}
                    </h4>
                  </button>
                );
              })}
            </div>

            {/* Selected Case Study Container */}
            <div className="rounded-2xl border border-[#20304C] bg-[#070B12] overflow-hidden shadow-2xl">
              
              {/* Header */}
              <div className="p-6 bg-[#10192A] border-b border-[#20304C]">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="px-2.5 py-0.5 rounded text-xs font-mono bg-purple-950 text-purple-300 border border-purple-800">
                        {selectedCase.category}
                      </span>
                      <h3 className="text-lg font-bold text-slate-100 font-mono">
                        {selectedCase.title}
                      </h3>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed max-w-4xl font-sans mt-2">
                      {selectedCase.explanation}
                    </p>
                  </div>

                  {/* Sub-view switcher (Diff / Diagnostics / Testbench) */}
                  <div className="flex items-center space-x-1 bg-[#070B12] p-1 rounded-lg border border-[#20304C]">
                    <button
                      onClick={() => setCaseViewMode('diff')}
                      className={`px-3 py-1.5 rounded text-xs font-mono transition ${
                        caseViewMode === 'diff'
                          ? 'bg-purple-950 text-purple-300 border border-purple-800'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      RTL Code Diff
                    </button>
                    <button
                      onClick={() => setCaseViewMode('diagnostic')}
                      className={`px-3 py-1.5 rounded text-xs font-mono transition ${
                        caseViewMode === 'diagnostic'
                          ? 'bg-amber-950 text-amber-300 border border-amber-800'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Agent Diagnostic
                    </button>
                    <button
                      onClick={() => setCaseViewMode('testbench')}
                      className={`px-3 py-1.5 rounded text-xs font-mono transition ${
                        caseViewMode === 'testbench'
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Cocotb Assertion
                    </button>
                  </div>
                </div>
              </div>

              {/* Body */}
              <div className="p-6">
                {caseViewMode === 'diff' && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <div className="flex items-center space-x-2 text-rose-400 text-xs font-mono font-bold mb-2">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Buggy Hardware Implementation (Flagged by EDA-Agent)</span>
                      </div>
                      <CodeBlock
                        code={selectedCase.badRTL}
                        language="verilog"
                        filename="buggy_module.v"
                        maxHeight="320px"
                      />
                    </div>

                    <div>
                      <div className="flex items-center space-x-2 text-emerald-400 text-xs font-mono font-bold mb-2">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Auto-Patched Synthesizable RTL (Verified 100%)</span>
                      </div>
                      <CodeBlock
                        code={selectedCase.goodRTL}
                        language="verilog"
                        filename="repaired_module.v"
                        maxHeight="320px"
                      />
                    </div>
                  </div>
                )}

                {caseViewMode === 'diagnostic' && (
                  <div className="space-y-4">
                    <div className="p-4 rounded-xl bg-[#10192A] border border-amber-500/40 space-y-2">
                      <div className="flex items-center space-x-2 text-xs font-mono font-bold text-amber-400">
                        <Terminal className="w-4 h-4" />
                        <span>Hardware Diagnostics Engine Root Cause Output</span>
                      </div>
                      <p className="text-xs font-mono text-slate-300 leading-relaxed">
                        {selectedCase.agentDiagnostic}
                      </p>
                    </div>
                  </div>
                )}

                {caseViewMode === 'testbench' && (
                  <div>
                    <div className="flex items-center space-x-2 text-emerald-400 text-xs font-mono font-bold mb-2">
                      <Code2 className="w-4 h-4" />
                      <span>Synthesized Cocotb Assertion Coroutine</span>
                    </div>
                    <CodeBlock
                      code={selectedCase.testbenchSnippet}
                      language="python"
                      filename={`test_${selectedCase.id}.py`}
                      maxHeight="320px"
                    />
                  </div>
                )}
              </div>

            </div>

          </div>
        )}

      </div>
    </section>
  );
};
