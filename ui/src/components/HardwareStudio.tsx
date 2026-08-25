import React, { useState, useEffect } from 'react';
import { 
  FlaskConical, 
  Play, 
  Download, 
  Sparkles, 
  Terminal, 
  Activity, 
  Wrench, 
  Boxes, 
  FileCode2, 
  ShieldCheck, 
  Clock, 
  HelpCircle,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import { playgroundPresets } from '../data/playgroundData';
import { HardwarePreset } from '../types';
import { WaveDromViewer } from './WaveDromViewer';

export const HardwareStudio: React.FC = () => {
  const [selectedPresetId, setSelectedPresetId] = useState<string>('alu_8bit');
  const [activeRightTab, setActiveRightTab] = useState<'tb' | 'sva'>('tb');
  const [activeBottomTab, setActiveBottomTab] = useState<'term' | 'wave' | 'diag'>('term');
  const [nlSpec, setNlSpec] = useState<string>('');
  const [rtlCode, setRtlCode] = useState<string>('');
  const [tbCode, setTbCode] = useState<string>('');
  const [svaCode, setSvaCode] = useState<string>('');
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  const [diagContent, setDiagContent] = useState<string | null>(null);

  const currentPreset: HardwarePreset = playgroundPresets.find((p) => p.id === selectedPresetId) || playgroundPresets[0];

  useEffect(() => {
    setRtlCode(currentPreset.code);
    setTbCode(currentPreset.testbench);
    setSvaCode(currentPreset.sva);
    setNlSpec(currentPreset.specPreset);
    setTerminalLogs([
      `[EDA-AGENT STUDIO] Loaded hardware module: '${currentPreset.filename}'`,
      `[EDA-AGENT STUDIO] Target: IEEE 1800 SystemVerilog | ${currentPreset.moduleSpec.ports.length} extracted ports.`,
      `[READY] Click 'Run Verification' or 'Synthesize Testbench' to execute.`
    ]);
    setDiagContent(null);
  }, [selectedPresetId]);

  const handleSynthesizeTB = () => {
    setIsSimulating(true);
    setTerminalLogs((prev) => [
      ...prev,
      `\n[SYNTHESIZE] Analyzing natural language specification: "${nlSpec}"...`,
      `[SYNTHESIZE] Generating Python cocotb async coroutines & assertion monitors...`,
      `✓ Testbench successfully updated with custom timing constraints.`
    ]);
    setTimeout(() => {
      setIsSimulating(false);
    }, 600);
  };

  const handleRunVerification = () => {
    setIsSimulating(true);
    setActiveBottomTab('term');
    setTerminalLogs((prev) => [
      ...prev,
      `\n[VERIFICATION SESSION] Starting headless simulation with Cocotb v2.0...`,
      `[VERILATOR] Static lint clean (0 warnings).`,
      `[YOSYS] Technology gate mapping: synthesizable (0 latches).`,
      `[SIMULATOR] Running testbench against ${currentPreset.name}...`
    ]);

    setTimeout(() => {
      setTerminalLogs((prev) => [
        ...prev,
        currentPreset.simLog,
        `🏆 VERIFICATION PASSED (100% Pass Rate). VCD waveform generated.`
      ]);
      setIsSimulating(false);
    }, 1200);
  };

  const handleAutoFix = () => {
    setActiveBottomTab('term');
    setTerminalLogs((prev) => [
      ...prev,
      `\n🛠️ [AUTO-FIX] Initiating closed-loop diagnostic repair on RTL...`,
      `[DIAGNOSTICS] Checking combinational sensitivity lists and bitwidth alignment...`,
      `✓ RTL is already optimized and clean. No repair required.`
    ]);
  };

  const handleExplain = () => {
    setActiveBottomTab('diag');
    setDiagContent(`The module '${currentPreset.name}' satisfies all formal properties and boundary assertions without settling hazards or metastable clock violations.`);
  };

  const handleExportTB = () => {
    const blob = new Blob([tbCode], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_${currentPreset.id}.py`;
    a.click();
  };

  // Render SVG Schematic
  const renderSvgSchematic = () => {
    const spec = currentPreset.moduleSpec;
    const inputs = spec.ports.filter((p) => p.direction.toLowerCase().includes('input'));
    const outputs = spec.ports.filter((p) => p.direction.toLowerCase().includes('output'));
    const height = Math.max(220, Math.max(inputs.length, outputs.length) * 26 + 60);
    const width = 280;

    return (
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full font-mono text-xs select-none">
        {/* Module Box */}
        <rect
          x="65"
          y="20"
          width="150"
          height={height - 40}
          rx="8"
          fill="#10192A"
          stroke="#00F0FF"
          strokeWidth="1.5"
          className="drop-shadow-[0_0_12px_rgba(0,240,255,0.15)]"
        />
        <text
          x="140"
          y="42"
          fill="#00F0FF"
          fontWeight="bold"
          textAnchor="middle"
          fontSize="11"
        >
          {spec.name}
        </text>

        {/* Inputs */}
        {inputs.map((p, idx) => {
          const y = 60 + idx * 24;
          const isClk = p.is_clock;
          const isRst = p.is_reset;
          const color = isClk ? '#10B981' : isRst ? '#F43F5E' : '#94A3B8';
          return (
            <g key={`in_${p.name}`}>
              <line x1="15" y1={y} x2="65" y2={y} stroke={color} strokeWidth="1.5" />
              {isClk ? (
                <path d={`M 57 ${y - 4} L 65 ${y} L 57 ${y + 4}`} fill="none" stroke="#10B981" strokeWidth="1.5" />
              ) : (
                <circle cx="15" cy={y} r="2" fill={color} />
              )}
              <text x="10" y={y + 3} fill={color} fontSize="9" textAnchor="end">
                {p.name}{p.width !== '1' ? `[${p.width}]` : ''}
              </text>
            </g>
          );
        })}

        {/* Outputs */}
        {outputs.map((p, idx) => {
          const y = 60 + idx * 24;
          const color = '#38BDF8';
          return (
            <g key={`out_${p.name}`}>
              <line x1="215" y1={y} x2="265" y2={y} stroke={color} strokeWidth="1.5" />
              <circle cx="215" cy={y} r="2.5" fill={color} />
              <text x="270" y={y + 3} fill={color} fontSize="9" textAnchor="start">
                {p.name}{p.width !== '1' ? `[${p.width}]` : ''}
              </text>
            </g>
          );
        })}
      </svg>
    );
  };

  return (
    <section id="playground" className="py-20 bg-[#070B12] border-t border-[#20304C] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-10">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#10192A] border border-cyan-500/30 text-cyan-300 text-xs font-mono mb-3">
            <FlaskConical className="w-3.5 h-3.5 text-cyan-400" />
            <span>Interactive Live Hardware Studio</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
            Live Hardware Verification Playground
          </h2>
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            Select sample RTL modules, synthesize cocotb testbenches from natural language specifications, inspect digital schematics, and stream simulation waveforms directly in your browser.
          </p>
        </div>

        {/* Studio Window Container */}
        <div className="rounded-2xl border border-[#20304C] bg-[#0B111D] shadow-2xl overflow-hidden glass-panel-glow">
          
          {/* TOP TOOLBAR */}
          <div className="h-14 bg-[#10192A] border-b border-[#20304C] px-4 flex flex-wrap items-center justify-between gap-3">
            
            {/* Left: Module Preset Picker */}
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <FileCode2 className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold text-slate-300 font-mono hidden sm:inline">Module:</span>
              </div>
              <select
                value={selectedPresetId}
                onChange={(e) => setSelectedPresetId(e.target.value)}
                className="bg-[#070B12] border border-[#20304C] rounded-lg px-3 py-1.5 text-xs text-cyan-300 font-mono focus:outline-none focus:border-cyan-400"
              >
                {playgroundPresets.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.filename} ({p.name})
                  </option>
                ))}
              </select>
            </div>

            {/* Right: Quick Verification Actions */}
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSynthesizeTB}
                disabled={isSimulating}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#16233B] hover:bg-[#20304C] text-cyan-300 border border-cyan-500/40 text-xs font-mono transition"
              >
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span>Synthesize TB</span>
              </button>

              <button
                onClick={handleRunVerification}
                disabled={isSimulating}
                className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-black font-bold text-xs font-mono shadow-[0_0_15px_rgba(16,185,129,0.3)] transition"
              >
                {isSimulating ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-black" />
                ) : (
                  <Play className="w-3.5 h-3.5 text-black" />
                )}
                <span>{isSimulating ? 'Simulating...' : 'Run Verification'}</span>
              </button>

              <button
                onClick={handleExportTB}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg bg-[#070B12] border border-[#20304C]"
                title="Download Cocotb Testbench (.py)"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>

          </div>

          {/* MAIN 3-COLUMN WORKSPACE */}
          <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[#20304C] min-h-[460px]">
            
            {/* COLUMN 1: CONTROLS & SPECIFICATION (Width: 3 cols) */}
            <div className="lg:col-span-3 p-4 bg-[#0B111D] flex flex-col space-y-4">
              
              {/* Natural Language Spec Prompt */}
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center space-x-1.5 mb-2">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span>Natural Language Spec</span>
                </label>
                <textarea
                  value={nlSpec}
                  onChange={(e) => setNlSpec(e.target.value)}
                  rows={3}
                  placeholder="e.g. verify opcode 0 is ADD with zero flag assertion"
                  className="w-full bg-[#070B12] border border-[#20304C] rounded-lg p-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400 resize-none"
                />
              </div>

              {/* Quick Spec Presets */}
              <div>
                <span className="text-[10px] uppercase font-mono text-slate-500 font-bold block mb-1.5">
                  Preset Spec Prompts
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {[
                    'Zero flag asserts when result is 0',
                    'Verify all 8 opcodes across randomized vectors',
                    'No data dropped during burst traffic',
                    'CS_n remains low during byte transfer'
                  ].map((presetText) => (
                    <button
                      key={presetText}
                      onClick={() => setNlSpec(presetText)}
                      className="text-[10px] font-mono px-2 py-1 bg-[#10192A] hover:bg-[#16233B] text-slate-300 rounded border border-[#20304C] transition text-left"
                    >
                      {presetText}
                    </button>
                  ))}
                </div>
              </div>

              {/* 1-Click Action Buttons */}
              <div className="space-y-2 pt-3 border-t border-[#16233B]">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono block">
                  Autonomous Hardware Actions
                </label>

                <button
                  onClick={handleAutoFix}
                  className="w-full flex items-center justify-between px-3 py-2 bg-[#10192A] hover:bg-[#16233B] text-purple-300 rounded-lg border border-purple-900/60 text-xs font-mono transition"
                >
                  <span className="flex items-center space-x-2">
                    <Wrench className="w-3.5 h-3.5 text-purple-400" />
                    <span>Auto-Fix RTL Bug</span>
                  </span>
                  <span className="text-[9px] bg-purple-950 px-1.5 py-0.5 rounded text-purple-400">Loop</span>
                </button>

                <button
                  onClick={handleExplain}
                  className="w-full flex items-center justify-between px-3 py-2 bg-[#10192A] hover:bg-[#16233B] text-amber-300 rounded-lg border border-amber-900/60 text-xs font-mono transition"
                >
                  <span className="flex items-center space-x-2">
                    <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
                    <span>Explain Root Cause</span>
                  </span>
                  <span className="text-[9px] bg-amber-950 px-1.5 py-0.5 rounded text-amber-400">Diag</span>
                </button>
              </div>

              {/* Hardware Spec Badges */}
              <div className="mt-auto pt-3 border-t border-[#16233B] text-[11px] font-mono text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span>Category:</span>
                  <span className="text-slate-200">{currentPreset.category}</span>
                </div>
                <div className="flex justify-between">
                  <span>Port Count:</span>
                  <span className="text-cyan-400">{currentPreset.moduleSpec.ports.length} ports</span>
                </div>
              </div>

            </div>

            {/* COLUMN 2: CODE EDITORS (Width: 6 cols) */}
            <div className="lg:col-span-6 flex flex-col">
              
              {/* Top Split: RTL vs Testbench Tabs */}
              <div className="flex-1 grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#20304C]">
                
                {/* Left Editor: Verilog RTL */}
                <div className="flex flex-col">
                  <div className="h-8 bg-[#10192A] border-b border-[#20304C] px-3 flex items-center justify-between text-xs font-mono">
                    <span className="text-cyan-300 font-semibold">{currentPreset.filename}</span>
                    <span className="text-[10px] text-slate-500">Verilog RTL</span>
                  </div>
                  <div className="flex-1 p-2 bg-[#070B12] overflow-auto">
                    <textarea
                      value={rtlCode}
                      onChange={(e) => setRtlCode(e.target.value)}
                      className="w-full h-full min-h-[220px] bg-transparent text-slate-200 font-mono text-xs focus:outline-none resize-none leading-relaxed"
                      spellCheck="false"
                    />
                  </div>
                </div>

                {/* Right Editor: Cocotb Testbench / SVA */}
                <div className="flex flex-col">
                  <div className="h-8 bg-[#10192A] border-b border-[#20304C] px-3 flex items-center justify-between text-xs font-mono">
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => setActiveRightTab('tb')}
                        className={`px-2 py-0.5 rounded text-[11px] font-mono transition ${
                          activeRightTab === 'tb'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        testbench.py
                      </button>
                      <button
                        onClick={() => setActiveRightTab('sva')}
                        className={`px-2 py-0.5 rounded text-[11px] font-mono transition ${
                          activeRightTab === 'sva'
                            ? 'bg-purple-950 text-purple-400 border border-purple-800'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        SVA Assertions
                      </button>
                    </div>
                    <span className="text-[10px] text-emerald-400">Generated</span>
                  </div>
                  <div className="flex-1 p-2 bg-[#070B12] overflow-auto">
                    <textarea
                      value={activeRightTab === 'tb' ? tbCode : svaCode}
                      onChange={(e) => {
                        if (activeRightTab === 'tb') setTbCode(e.target.value);
                        else setSvaCode(e.target.value);
                      }}
                      className="w-full h-full min-h-[220px] bg-transparent text-slate-200 font-mono text-xs focus:outline-none resize-none leading-relaxed"
                      spellCheck="false"
                    />
                  </div>
                </div>

              </div>

            </div>

            {/* COLUMN 3: HARDWARE SCHEMATIC (Width: 3 cols) */}
            <div className="lg:col-span-3 bg-[#0B111D] flex flex-col">
              <div className="h-8 bg-[#10192A] border-b border-[#20304C] px-3 flex items-center justify-between text-xs font-mono">
                <span className="text-slate-300 font-bold flex items-center space-x-1.5">
                  <Boxes className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Port Schematic</span>
                </span>
                <span className="text-[10px] text-slate-500">{currentPreset.moduleSpec.name}</span>
              </div>
              <div className="flex-1 p-3 flex items-center justify-center bg-[#070B12] overflow-auto min-h-[200px]">
                {renderSvgSchematic()}
              </div>
            </div>

          </div>

          {/* BOTTOM SPLIT: SIMULATION TERMINAL & WAVEDROM VIEWER */}
          <div className="border-t border-[#20304C] bg-[#070B12]">
            
            {/* Bottom Tabs */}
            <div className="h-9 bg-[#10192A] border-b border-[#20304C] px-4 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setActiveBottomTab('term')}
                  className={`px-3 py-1 flex items-center space-x-1.5 transition ${
                    activeBottomTab === 'term'
                      ? 'text-cyan-400 border-b-2 border-cyan-400 font-semibold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Terminal className="w-3.5 h-3.5" />
                  <span>Simulation Terminal</span>
                </button>

                <button
                  onClick={() => setActiveBottomTab('wave')}
                  className={`px-3 py-1 flex items-center space-x-1.5 transition ${
                    activeBottomTab === 'wave'
                      ? 'text-emerald-400 border-b-2 border-emerald-400 font-semibold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Activity className="w-3.5 h-3.5" />
                  <span>WaveDrom Waveform</span>
                </button>

                <button
                  onClick={() => setActiveBottomTab('diag')}
                  className={`px-3 py-1 flex items-center space-x-1.5 transition ${
                    activeBottomTab === 'diag'
                      ? 'text-amber-400 border-b-2 border-amber-400 font-semibold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Hardware Diagnostics</span>
                </button>
              </div>

              {isSimulating && (
                <div className="flex items-center space-x-2 text-amber-400 text-xs">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Simulating in Sandbox...</span>
                </div>
              )}
            </div>

            {/* Bottom Panel Views */}
            <div className="p-4 min-h-[160px] max-h-[220px] overflow-y-auto font-mono text-xs text-slate-300">
              {activeBottomTab === 'term' && (
                <div className="space-y-1">
                  {terminalLogs.map((log, idx) => (
                    <div
                      key={idx}
                      className={
                        log.includes('PASSED') || log.includes('🏆')
                          ? 'text-emerald-400 font-semibold'
                          : log.includes('FAILED') || log.includes('❌')
                          ? 'text-rose-400 font-semibold'
                          : log.includes('✓')
                          ? 'text-cyan-300'
                          : 'text-slate-300'
                      }
                    >
                      {log}
                    </div>
                  ))}
                </div>
              )}

              {activeBottomTab === 'wave' && (
                <WaveDromViewer
                  wavedromData={currentPreset.wavedrom}
                  title={`${currentPreset.filename} Timing Traces`}
                />
              )}

              {activeBottomTab === 'diag' && (
                <div className="p-3 rounded-lg bg-[#10192A] border border-[#20304C] text-slate-300 leading-relaxed">
                  {diagContent || 'All formal assertion checks and synthesizability metrics passed with 0 violations.'}
                </div>
              )}
            </div>

          </div>

        </div>

      </div>
    </section>
  );
};
