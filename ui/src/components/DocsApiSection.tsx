import React, { useState } from 'react';
import { 
  Code2, 
  Layers, 
  BookOpen, 
  ShieldCheck, 
  Terminal, 
  Cpu, 
  ChevronRight, 
  CheckCircle2,
  FileCode
} from 'lucide-react';
import { apiDocs, hardwareDesignRules } from '../data/docsData';
import { CodeBlock } from './CodeBlock';

export const DocsApiSection: React.FC = () => {
  const [selectedPkgIndex, setSelectedPkgIndex] = useState<number>(0);
  const currentPkg = apiDocs[selectedPkgIndex];

  return (
    <section id="docs" className="py-20 bg-[#070B12] border-t border-[#20304C] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#10192A] border border-cyan-500/30 text-cyan-300 text-xs font-mono mb-3">
            <Code2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Python Core API Reference</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
            Developer Documentation & Module API
          </h2>
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            Directly import and script EDA-Agent components inside your custom Python test harnesses and verification infrastructure.
          </p>
        </div>

        {/* SECTION 1: HARDWARE DESIGN RULES */}
        <div className="mb-14 p-6 rounded-2xl border border-[#20304C] bg-[#0B111D] shadow-xl">
          <div className="flex items-center space-x-2 text-sm font-bold text-cyan-300 font-mono mb-4">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <span>Hardware Engineering Rules Enforced by EDA-Agent</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {hardwareDesignRules.map((rule, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-[#070B12] border border-[#20304C] space-y-1">
                <div className="flex items-center space-x-2 text-xs font-bold text-slate-200 font-mono">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>{rule.rule}</span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed pl-5 font-sans">
                  {rule.detail}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION 2: PYTHON API PACKAGES EXPLORER */}
        <div className="rounded-2xl border border-[#20304C] bg-[#0B111D] overflow-hidden shadow-2xl">
          
          <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[#20304C] min-h-[500px]">
            
            {/* Left: Package List Sidebar (4 cols) */}
            <div className="lg:col-span-4 p-4 bg-[#10192A] space-y-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono block px-3 py-1">
                Core Python Packages
              </span>

              {apiDocs.map((pkg, idx) => {
                const isSelected = idx === selectedPkgIndex;
                return (
                  <button
                    key={pkg.package}
                    onClick={() => setSelectedPkgIndex(idx)}
                    className={`w-full text-left p-3 rounded-xl transition-all ${
                      isSelected
                        ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-500/50 shadow-md'
                        : 'text-slate-400 hover:bg-[#070B12] hover:text-slate-200'
                    }`}
                  >
                    <div className="font-mono text-xs font-bold truncate">
                      {pkg.package}
                    </div>
                    <div className="text-[11px] font-sans text-slate-400 truncate mt-0.5">
                      {pkg.title}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Right: Classes & Methods Documentation (8 cols) */}
            <div className="lg:col-span-8 p-6 bg-[#070B12] space-y-8 overflow-y-auto max-h-[700px]">
              
              <div>
                <h3 className="text-xl font-bold font-mono text-cyan-300">
                  {currentPkg.package}
                </h3>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  {currentPkg.description}
                </p>
              </div>

              {/* Classes in package */}
              <div className="space-y-6">
                {currentPkg.classes.map((cls) => (
                  <div key={cls.name} className="p-5 rounded-xl bg-[#0B111D] border border-[#20304C] space-y-4">
                    
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-400 border border-purple-800">
                          CLASS
                        </span>
                        <h4 className="text-base font-bold text-slate-100 font-mono">
                          {cls.name}
                        </h4>
                      </div>
                      <p className="text-xs text-slate-400 font-sans mt-1.5">
                        {cls.summary}
                      </p>
                    </div>

                    {/* Method List */}
                    <div className="space-y-2">
                      <span className="text-[10px] uppercase font-mono font-bold text-slate-400 block">
                        Public Methods
                      </span>
                      <div className="space-y-2">
                        {cls.methods.map((m, mIdx) => (
                          <div key={mIdx} className="p-3 rounded-lg bg-[#070B12] border border-[#16233B] font-mono text-xs space-y-1">
                            <div className="text-cyan-300 font-bold overflow-x-auto">
                              {m.signature}
                            </div>
                            <div className="text-[11px] text-slate-400 font-sans">
                              {m.description}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Python usage snippet */}
                    <div>
                      <span className="text-[10px] uppercase font-mono font-bold text-slate-400 block mb-1.5">
                        Usage Example
                      </span>
                      <CodeBlock
                        code={cls.exampleCode}
                        language="python"
                        filename="example_usage.py"
                        maxHeight="220px"
                      />
                    </div>

                  </div>
                ))}
              </div>

            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
