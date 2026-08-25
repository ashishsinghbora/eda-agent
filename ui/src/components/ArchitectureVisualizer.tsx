import React, { useState } from 'react';
import { 
  Layers, 
  FileCode2, 
  ShieldAlert, 
  Cpu, 
  FlaskConical, 
  PlaySquare, 
  Wrench, 
  Clock, 
  ArrowRight, 
  CheckCircle2, 
  RefreshCw, 
  Terminal, 
  Sparkles,
  Info,
  ChevronRight
} from 'lucide-react';
import { pipelineStages, pipelineModes } from '../data/architectureData';
import { PipelineStage } from '../types';

export const ArchitectureVisualizer: React.FC = () => {
  const [selectedModeId, setSelectedModeId] = useState('verify');
  const [selectedStageId, setSelectedStageId] = useState('parser');

  const selectedMode = pipelineModes.find((m) => m.id === selectedModeId) || pipelineModes[0];
  const selectedStage: PipelineStage = pipelineStages.find((s) => s.id === selectedStageId) || pipelineStages[0];

  const getStageIcon = (iconName: string, color: string) => {
    const props = { className: `w-5 h-5 ${getColorClass(color).icon}` };
    switch (iconName) {
      case 'FileCode2': return <FileCode2 {...props} />;
      case 'ShieldAlert': return <ShieldAlert {...props} />;
      case 'Cpu': return <Cpu {...props} />;
      case 'FlaskConical': return <FlaskConical {...props} />;
      case 'PlaySquare': return <PlaySquare {...props} />;
      case 'Wrench': return <Wrench {...props} />;
      case 'Clock': return <Clock {...props} />;
      default: return <Layers {...props} />;
    }
  };

  const getColorClass = (color: string) => {
    switch (color) {
      case 'cyan':
        return {
          bg: 'bg-cyan-950/50',
          border: 'border-cyan-500/50',
          text: 'text-cyan-300',
          icon: 'text-cyan-400',
          badge: 'bg-cyan-950 text-cyan-400 border-cyan-800',
          glow: 'shadow-[0_0_15px_rgba(0,240,255,0.2)]'
        };
      case 'purple':
        return {
          bg: 'bg-purple-950/50',
          border: 'border-purple-500/50',
          text: 'text-purple-300',
          icon: 'text-purple-400',
          badge: 'bg-purple-950 text-purple-400 border-purple-800',
          glow: 'shadow-[0_0_15px_rgba(168,85,247,0.2)]'
        };
      case 'amber':
        return {
          bg: 'bg-amber-950/50',
          border: 'border-amber-500/50',
          text: 'text-amber-300',
          icon: 'text-amber-400',
          badge: 'bg-amber-950 text-amber-400 border-amber-800',
          glow: 'shadow-[0_0_15px_rgba(245,158,11,0.2)]'
        };
      case 'emerald':
        return {
          bg: 'bg-emerald-950/50',
          border: 'border-emerald-500/50',
          text: 'text-emerald-300',
          icon: 'text-emerald-400',
          badge: 'bg-emerald-950 text-emerald-400 border-emerald-800',
          glow: 'shadow-[0_0_15px_rgba(16,185,129,0.2)]'
        };
      case 'rose':
        return {
          bg: 'bg-rose-950/50',
          border: 'border-rose-500/50',
          text: 'text-rose-300',
          icon: 'text-rose-400',
          badge: 'bg-rose-950 text-rose-400 border-rose-800',
          glow: 'shadow-[0_0_15px_rgba(244,63,94,0.2)]'
        };
      default:
        return {
          bg: 'bg-blue-950/50',
          border: 'border-blue-500/50',
          text: 'text-blue-300',
          icon: 'text-blue-400',
          badge: 'bg-blue-950 text-blue-400 border-blue-800',
          glow: 'shadow-[0_0_15px_rgba(59,130,246,0.2)]'
        };
    }
  };

  return (
    <section id="architecture" className="py-20 bg-[#070B12] border-t border-[#20304C] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#10192A] border border-cyan-500/30 text-cyan-300 text-xs font-mono mb-3">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>Multi-Stage Autonomous Pipeline</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
            Interactive Architecture Visualizer
          </h2>
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            Click any pipeline stage below to inspect its internal logic, input schemas, diagnostic output tokens, and automated recovery loops.
          </p>
        </div>

        {/* Pipeline Mode Switcher */}
        <div className="flex flex-wrap justify-center gap-2 mb-10">
          {pipelineModes.map((mode) => {
            const isSelected = mode.id === selectedModeId;
            return (
              <button
                key={mode.id}
                onClick={() => {
                  setSelectedModeId(mode.id);
                  if (!mode.activeStages.includes(selectedStageId)) {
                    setSelectedStageId(mode.activeStages[0]);
                  }
                }}
                className={`px-4 py-2 rounded-xl text-xs font-mono transition-all ${
                  isSelected
                    ? 'bg-gradient-to-r from-cyan-950 to-[#10192A] text-cyan-300 border border-cyan-400 shadow-[0_0_15px_rgba(0,240,255,0.2)] font-semibold'
                    : 'bg-[#0B111D] hover:bg-[#10192A] text-slate-400 border border-[#20304C]'
                }`}
              >
                {mode.title}
              </button>
            );
          })}
        </div>

        {/* Selected Mode Banner Description */}
        <div className="mb-8 p-4 rounded-xl bg-[#10192A]/80 border border-[#20304C] text-xs text-slate-300 font-sans flex items-start space-x-3 max-w-4xl mx-auto">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">{selectedMode.description}</p>
        </div>

        {/* Interactive Pipeline Stages Grid / Horizontal Flow */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {pipelineStages.map((stage, idx) => {
            const isSelected = stage.id === selectedStageId;
            const isInCurrentMode = selectedMode.activeStages.includes(stage.id);
            const style = getColorClass(stage.color);

            return (
              <div
                key={stage.id}
                onClick={() => setSelectedStageId(stage.id)}
                className={`relative p-4 rounded-xl border transition-all cursor-pointer select-none group ${
                  isSelected
                    ? `${style.bg} ${style.border} ${style.glow} scale-[1.02]`
                    : isInCurrentMode
                    ? 'bg-[#0B111D] border-[#20304C] hover:border-cyan-500/40 hover:bg-[#10192A]'
                    : 'bg-[#0B111D]/40 border-[#20304C]/40 opacity-40 hover:opacity-75'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className="p-2 rounded-lg bg-[#070B12] border border-[#20304C]">
                      {getStageIcon(stage.iconName, stage.color)}
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 font-bold">
                      STAGE {idx + 1}
                    </span>
                  </div>
                  {isSelected && (
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                  )}
                </div>

                <h4 className="font-bold text-sm text-slate-100 mb-1 group-hover:text-cyan-300 transition">
                  {stage.title}
                </h4>
                <p className="text-[11px] text-slate-400 leading-snug line-clamp-2">
                  {stage.subtitle}
                </p>

                <div className="mt-3 flex items-center justify-between text-[10px] font-mono text-slate-500 pt-2 border-t border-[#16233B]">
                  <span>{isInCurrentMode ? 'Active Flow' : 'Bypassed'}</span>
                  <ChevronRight className={`w-3.5 h-3.5 ${isSelected ? 'text-cyan-400' : 'text-slate-600'}`} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Detailed Stage Drilldown Panel */}
        <div className="rounded-2xl border border-[#20304C] bg-[#0B111D] overflow-hidden shadow-2xl glass-panel-glow">
          
          {/* Header */}
          <div className="px-6 py-4 bg-[#10192A] border-b border-[#20304C] flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-[#070B12] border border-cyan-500/40">
                {getStageIcon(selectedStage.iconName, selectedStage.color)}
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-bold text-slate-100 font-mono">
                    {selectedStage.title}
                  </h3>
                  <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                    {selectedStage.id.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Python Module: <code className="text-cyan-300">{selectedStage.modulePath}</code>
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono text-slate-400">Trigger Command:</span>
              <code className="text-xs font-mono px-2.5 py-1 rounded bg-[#070B12] text-amber-300 border border-[#20304C]">
                {selectedStage.toolCommand}
              </code>
            </div>
          </div>

          {/* Drilldown Content Body */}
          <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Col 1 & 2: Overview & Sample Diagnostic */}
            <div className="lg:col-span-2 space-y-5">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-2">
                  Stage Purpose & Architecture
                </h4>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {selectedStage.description}
                </p>
              </div>

              {/* Sample Diagnostic Output */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono mb-2 flex items-center space-x-1.5">
                  <Terminal className="w-3.5 h-3.5" />
                  <span>Real Diagnostic & Log Payload</span>
                </h4>
                <div className="p-3.5 rounded-lg bg-[#070B12] border border-[#20304C] font-mono text-xs text-slate-300 leading-relaxed overflow-x-auto">
                  {selectedStage.sampleDiagnostic}
                </div>
              </div>

              {/* Autonomous Recovery Action */}
              <div className="p-4 rounded-xl bg-purple-950/30 border border-purple-800/50 space-y-1">
                <div className="flex items-center space-x-2 text-xs font-mono font-bold text-purple-400">
                  <Wrench className="w-4 h-4" />
                  <span>Autonomous Error Recovery Loop</span>
                </div>
                <p className="text-xs text-purple-200/90 leading-relaxed">
                  {selectedStage.recoveryAction}
                </p>
              </div>
            </div>

            {/* Col 3: Inputs & Outputs Schema */}
            <div className="space-y-4 bg-[#070B12] p-5 rounded-xl border border-[#20304C]">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 font-mono mb-2.5 flex items-center space-x-1">
                  <ArrowRight className="w-3.5 h-3.5" />
                  <span>Input Artifacts</span>
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-300 font-mono">
                  {selectedStage.inputs.map((inp, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className="text-emerald-400 mt-0.5">•</span>
                      <span>{inp}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="pt-4 border-t border-[#16233B]">
                <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono mb-2.5 flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Output Dataclass / Report</span>
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-300 font-mono">
                  {selectedStage.outputs.map((out, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className="text-cyan-400 mt-0.5">•</span>
                      <span>{out}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
