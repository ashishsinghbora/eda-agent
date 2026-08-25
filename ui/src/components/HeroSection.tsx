import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  ChevronRight, 
  ChevronLeft, 
  Terminal, 
  Sparkles, 
  ShieldCheck, 
  Cpu, 
  Wrench, 
  Layers, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Activity, 
  ExternalLink,
  ArrowRight,
  Zap,
  Code2
} from 'lucide-react';
import { WaveDromViewer } from './WaveDromViewer';

interface HeroSectionProps {
  onNavigate: (section: string) => void;
}

interface StepData {
  step: number;
  stageName: string;
  badge: string;
  badgeColor: 'cyan' | 'purple' | 'amber' | 'rose' | 'emerald';
  logLines: string[];
  diff?: {
    filename: string;
    removed: string[];
    added: string[];
  };
  wavedrom?: any;
}

const simulationSteps: StepData[] = [
  {
    step: 1,
    stageName: 'RTL Interface Extraction',
    badge: 'AST Parser',
    badgeColor: 'cyan',
    logLines: [
      '$ eda-agent verify examples/rtl/alu_8bit.v --max-retries 3 --dump-vcd',
      '[EDA-AGENT] Initializing autonomous verification loop...',
      '[STAGE 1/6] Scanning RTL source: `examples/rtl/alu_8bit.v`',
      '  └── Extracted module: `alu_8bit` (Parameterized DATA_WIDTH=8)',
      '  └── Clocks: 1 (clk) | Active-low Resets: 1 (rst_n)',
      '  └── Extracted 8 input/output ports: a[7:0], b[7:0], opcode[2:0], result[7:0], zero, carry, overflow.',
      '✓ Interface schema extracted successfully.'
    ]
  },
  {
    step: 2,
    stageName: 'Verilator Static Linting',
    badge: 'Verilator 5.0',
    badgeColor: 'purple',
    logLines: [
      '[STAGE 2/6] Invoking Verilator --lint-only -Wall --bbox-sys',
      '%Warning-WIDTHCONCAT: alu_8bit.v:32:15: Operator ADD expects 8 bits on RHS, but LHS has 9 bits.',
      '  └── Line 32: temp_result = a + b; result <= temp_result;',
      '  └── Notice: Arithmetic carry output bit not cleanly masked to 8-bit bus boundary.',
      '! Static Lint Flagged: 1 warning token parsed into structured diagnostic.'
    ]
  },
  {
    step: 3,
    stageName: 'Yosys Gate-Level Synthesis Check',
    badge: 'Yosys HQ',
    badgeColor: 'amber',
    logLines: [
      '[STAGE 3/6] Running Yosys gate-level synthesizability check...',
      '  └── Command: yosys -p "read_verilog -sv rtl.v; proc; opt; stat"',
      '  └── Cell Mapping: 11 $_DFF_P_, 32 $_MUX_, 18 $_NAND_, 8 $_XOR_',
      '  └── Latch Detection: 0 transparent latches inferred (clean hierarchy)',
      '✓ Gate-level check passed: RTL is 100% physically synthesizable.'
    ]
  },
  {
    step: 4,
    stageName: 'Autonomous Cocotb Testbench Synthesis',
    badge: 'cocotb 2.0',
    badgeColor: 'emerald',
    logLines: [
      '[STAGE 4/6] Synthesizing Python cocotb testbench `sim/test_alu_8bit.py`...',
      '  └── Injected Clock coroutine: 100MHz (10ns period)',
      '  └── Injected Reset coroutine: 20ns active-low assertion',
      '  └── Injected Golden Reference Software Model: `golden_alu_model(a, b, op)`',
      '  └── Injected Randomized Stimulus: 120 randomized vectors across all 8 opcodes.',
      '✓ Testbench synthesis completed (145 lines of async Python).'
    ]
  },
  {
    step: 5,
    stageName: 'Simulation Iteration 1 (Bug Caught)',
    badge: 'Icarus Verilog',
    badgeColor: 'rose',
    logLines: [
      '[STAGE 5/6] Executing Headless Simulation Iteration 1...',
      '  └── Simulator: Icarus Verilog (vvp) + Cocotb v2.0 harness',
      '  └── [Cycle 124, T=1240.00ns] Testing Opcode 0 (ADD) with a=0xFF, b=0x01:',
      '  ❌ AssertionError: Expected result 0x00 with carry=1, but observed result=0x100!',
      '  └── Status: Simulation FAILED (Pass Rate: 82.5%)',
      '⚡ Triggering Closed-Loop Hardware Diagnostic & Auto-Repair Engine...'
    ]
  },
  {
    step: 6,
    stageName: 'Closed-Loop RTL Self-Repair & Patching',
    badge: 'AI Self-Repair',
    badgeColor: 'purple',
    logLines: [
      '[STAGE 6/6] Hardware Diagnostics Translator analyzing traceback:',
      '  └── Root Cause: 9-bit arithmetic overflow leaking into 8-bit result bus.',
      '  └── Synthesizing surgical RTL patch...',
      '  └── Applying diff to `examples/rtl/alu_8bit.v` (Line 32):',
      '      - result <= temp_result;',
      '      + result <= temp_result[DATA_WIDTH-1:0];',
      '✓ RTL patch successfully applied. Re-running headless simulation harness...'
    ],
    diff: {
      filename: 'examples/rtl/alu_8bit.v',
      removed: [
        '// Line 32: Unmasked 9-bit assignment',
        'result <= temp_result;'
      ],
      added: [
        '// Line 32: Explicit 8-bit boundary slice & carry split',
        'result <= temp_result[DATA_WIDTH-1:0];'
      ]
    }
  },
  {
    step: 7,
    stageName: 'Simulation Iteration 2: 100% Verification Pass',
    badge: 'VERIFIED',
    badgeColor: 'emerald',
    logLines: [
      '========================================================================',
      '[ITERATION 2] Executing patched simulation with Icarus Verilog...',
      '  ✓ test_reset_behavior .................................... PASSED [ 25%]',
      '  ✓ test_alu_exhaustive_opcodes ............................ PASSED [ 50%]',
      '  ✓ test_randomized_boundary_vectors (120/120 vectors) ..... PASSED [ 75%]',
      '  ✓ test_corner_cases (overflow & zero flag assertion) ..... PASSED [100%]',
      '========================================================================',
      '🏆 VERIFICATION SUCCEEDED in 2 attempts! (100% Pass Rate)',
      '📦 Digital VCD Waveform captured and saved to `sim/alu_8bit.vcd`.'
    ],
    wavedrom: {
      signal: [
        { name: "clk", wave: "p......." },
        { name: "rst_n", wave: "0.1....." },
        { name: "opcode[2:0]", wave: "=...==..", data: ["ADD (0)", "SUB (1)", "AND (2)"] },
        { name: "a[7:0]", wave: "x.======.", data: ["0xFF", "0x55", "0x12", "0x00"] },
        { name: "b[7:0]", wave: "x.======.", data: ["0x01", "0x15", "0x34", "0x80"] },
        { name: "result[7:0]", wave: "x.======.", data: ["0x00", "0x40", "0x10", "0x80"] },
        { name: "carry", wave: "0.1.0..." },
        { name: "zero", wave: "0.1.0..." }
      ],
      head: { text: "Verified Digital Waveform Output (alu_8bit.vcd)" },
      foot: { tick: 0 }
    }
  }
];

export const HeroSection: React.FC<HeroSectionProps> = ({ onNavigate }) => {
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(2000); // ms per step
  const [activeTab, setActiveTab] = useState<'terminal' | 'diff' | 'wave'>('terminal');
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setTimeout(() => {
        setCurrentStepIdx((prev) => {
          if (prev >= simulationSteps.length - 1) {
            return 0; // loop
          }
          return prev + 1;
        });
      }, playbackSpeed);
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isPlaying, currentStepIdx, playbackSpeed]);

  const currentStep = simulationSteps[currentStepIdx];

  const handleManualStep = (index: number) => {
    setIsPlaying(false);
    setCurrentStepIdx(index);
  };

  return (
    <section className="relative pt-28 pb-20 overflow-hidden cyber-grid">
      {/* Radial glow backdrop */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-cyan-500/10 via-purple-500/10 to-transparent blur-[120px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        {/* Top Badges */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-6">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#10192A] border border-cyan-500/30 text-cyan-300 text-xs font-mono shadow-[0_0_15px_rgba(0,240,255,0.15)]">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            <span>Open-Source Hardware Verification Framework</span>
          </div>

          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#10192A] border border-purple-500/30 text-purple-300 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>cocotb v2.0 + Verilator + Yosys</span>
          </div>
        </div>

        {/* Main Headline */}
        <div className="text-center max-w-4xl mx-auto mb-8">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-100 leading-[1.15] mb-6">
            Autonomous VLSI Verification &{' '}
            <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-purple-400 bg-clip-text text-transparent">
              RTL Self-Repair
            </span>{' '}
            at Hardware Scale
          </h1>

          <p className="text-base sm:text-lg text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Bridge SystemVerilog/Verilog hardware designs with modern Python <code className="text-cyan-300 font-mono bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800">cocotb</code> workflows. Automated RTL interface parsing, Verilator linting, Yosys gate-level synthesizability checks, autonomous testbench generation, STA diagnostics, and closed-loop simulation self-repair.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4 mb-14">
          <button
            onClick={() => onNavigate('cli')}
            className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-semibold text-sm shadow-[0_0_25px_rgba(0,240,255,0.35)] transition-all hover:scale-105 active:scale-95 font-mono"
          >
            <Zap className="w-4 h-4 text-black" />
            <span>Get Started</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => onNavigate('playground')}
            className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-[#10192A] hover:bg-[#16233B] text-slate-100 border border-[#20304C] hover:border-cyan-500/50 font-semibold text-sm transition-all font-mono shadow-md"
          >
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>Live Hardware Studio</span>
          </button>

          <a
            href="https://github.com/ashishsinghbora/eda-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 px-5 py-3 rounded-xl bg-[#0B111D] hover:bg-[#10192A] text-slate-300 hover:text-white border border-[#20304C] text-sm font-mono transition"
          >
            <span>Star on GitHub</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
          </a>
        </div>

        {/* Interactive Simulation Terminal / Animated CLI Preview */}
        <div className="max-w-5xl mx-auto rounded-2xl border border-[#20304C] bg-[#0B111D] shadow-2xl overflow-hidden glass-panel-glow">
          
          {/* Terminal Window Header Bar */}
          <div className="px-4 py-3 bg-[#10192A] border-b border-[#20304C] flex flex-wrap items-center justify-between gap-2">
            
            {/* Window controls & command title */}
            <div className="flex items-center space-x-3">
              <div className="flex space-x-1.5">
                <div className="w-3 h-3 rounded-full bg-rose-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
              </div>
              <div className="flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <span className="font-mono text-xs font-semibold text-slate-200">
                  eda-agent verify examples/rtl/alu_8bit.v
                </span>
              </div>
            </div>

            {/* View Tab Selector */}
            <div className="flex items-center space-x-1 bg-[#070B12] p-1 rounded-lg border border-[#20304C]">
              <button
                onClick={() => setActiveTab('terminal')}
                className={`px-2.5 py-1 rounded text-xs font-mono transition ${
                  activeTab === 'terminal'
                    ? 'bg-cyan-950 text-cyan-400 border border-cyan-800'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                CLI Output
              </button>
              <button
                onClick={() => setActiveTab('diff')}
                className={`px-2.5 py-1 rounded text-xs font-mono transition ${
                  activeTab === 'diff'
                    ? 'bg-purple-950 text-purple-400 border border-purple-800'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                RTL Patch Diff
              </button>
              <button
                onClick={() => setActiveTab('wave')}
                className={`px-2.5 py-1 rounded text-xs font-mono transition ${
                  activeTab === 'wave'
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Waveform
              </button>
            </div>

            {/* Playback Controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentStepIdx((prev) => Math.max(0, prev - 1))}
                disabled={currentStepIdx === 0}
                className="p-1 rounded text-slate-400 hover:text-white disabled:opacity-30"
                title="Previous step"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="flex items-center space-x-1 px-2.5 py-1 rounded bg-[#16233B] hover:bg-[#20304C] text-cyan-300 text-xs font-mono border border-[#20304C]"
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 text-emerald-400" />}
                <span>{isPlaying ? 'Pause' : 'Play'}</span>
              </button>

              <button
                onClick={() => setCurrentStepIdx((prev) => Math.min(simulationSteps.length - 1, prev + 1))}
                disabled={currentStepIdx === simulationSteps.length - 1}
                className="p-1 rounded text-slate-400 hover:text-white disabled:opacity-30"
                title="Next step"
              >
                <ChevronRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => {
                  setCurrentStepIdx(0);
                  setIsPlaying(true);
                }}
                className="p-1 rounded text-slate-400 hover:text-white"
                title="Replay sequence"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>

          </div>

          {/* Interactive Step Timeline Scrubber */}
          <div className="px-4 py-2 bg-[#0E1626] border-b border-[#20304C] flex items-center justify-between overflow-x-auto gap-2">
            {simulationSteps.map((step, idx) => {
              const isCurrent = idx === currentStepIdx;
              const isPast = idx < currentStepIdx;
              return (
                <button
                  key={step.step}
                  onClick={() => handleManualStep(idx)}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono whitespace-nowrap transition-all ${
                    isCurrent
                      ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(0,240,255,0.2)]'
                      : isPast
                      ? 'text-slate-400 hover:text-slate-200'
                      : 'text-slate-600 hover:text-slate-400'
                  }`}
                >
                  <span
                    className={`w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold ${
                      isCurrent
                        ? 'bg-cyan-400 text-black'
                        : isPast
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : 'bg-[#10192A] text-slate-500 border border-[#20304C]'
                    }`}
                  >
                    {idx + 1}
                  </span>
                  <span>{step.stageName}</span>
                </button>
              );
            })}
          </div>

          {/* Body: Terminal Output or Diff or WaveDrom */}
          <div className="p-5 font-mono text-xs min-h-[300px] max-h-[360px] overflow-y-auto bg-[#070B12]">
            {activeTab === 'terminal' && (
              <div className="space-y-1.5">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#16233B]">
                  <div className="flex items-center space-x-2">
                    <span className="text-slate-500">Stage {currentStep.step} of 7:</span>
                    <span className="font-bold text-cyan-300">{currentStep.stageName}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-950/80 text-cyan-400 border border-cyan-800/80">
                    {currentStep.badge}
                  </span>
                </div>

                {currentStep.logLines.map((line, lIdx) => {
                  let colorClass = 'text-slate-300';
                  if (line.startsWith('$')) colorClass = 'text-cyan-400 font-semibold';
                  else if (line.includes('PASSED') || line.includes('✓') || line.includes('🏆')) colorClass = 'text-emerald-400 font-semibold';
                  else if (line.includes('FAILED') || line.includes('❌') || line.includes('AssertionError')) colorClass = 'text-rose-400 font-semibold';
                  else if (line.includes('%Warning') || line.includes('!')) colorClass = 'text-amber-400';
                  else if (line.includes('[STAGE') || line.includes('⚡')) colorClass = 'text-purple-300';

                  return (
                    <div key={lIdx} className={`leading-relaxed ${colorClass}`}>
                      {line}
                    </div>
                  );
                })}
              </div>
            )}

            {activeTab === 'diff' && (
              <div>
                <div className="flex items-center justify-between pb-2 mb-3 border-b border-[#16233B]">
                  <span className="text-purple-300 font-semibold">Autonomous Surgical RTL Patch:</span>
                  <span className="text-slate-400 text-[11px]">examples/rtl/alu_8bit.v</span>
                </div>

                {currentStep.diff ? (
                  <div className="rounded border border-[#20304C] bg-[#0B111D] p-3 space-y-1">
                    {currentStep.diff.removed.map((line, idx) => (
                      <div key={`rem_${idx}`} className="text-rose-400 bg-rose-950/30 px-2 py-0.5 rounded font-mono">
                        - {line}
                      </div>
                    ))}
                    {currentStep.diff.added.map((line, idx) => (
                      <div key={`add_${idx}`} className="text-emerald-400 bg-emerald-950/30 px-2 py-0.5 rounded font-mono">
                        + {line}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-400 py-8 text-center">
                    No active RTL code modifications in Stage {currentStep.step}. Advance to Stage 6 to view the autonomous repair diff.
                  </div>
                )}
              </div>
            )}

            {activeTab === 'wave' && (
              <div>
                {currentStep.wavedrom ? (
                  <WaveDromViewer wavedromData={currentStep.wavedrom} title="Simulation VCD Waveform Capture" />
                ) : (
                  <div className="text-slate-400 py-10 text-center">
                    Waveform is generated at completion of verification. Step forward to Stage 7 to inspect digital waveforms!
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Terminal Bottom Status Bar */}
          <div className="px-4 py-2 bg-[#10192A] border-t border-[#20304C] flex items-center justify-between text-[11px] font-mono text-slate-400">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Simulation Sandbox: Ready</span>
            </div>
            <div className="flex items-center space-x-4">
              <span>Target: IEEE 1800 SystemVerilog</span>
              <span>Backend: Airgapped Ollama / Local EDA</span>
            </div>
          </div>

        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-12">
          
          <div className="p-5 rounded-xl border border-[#20304C] bg-[#0B111D]/80 backdrop-blur hover:border-cyan-500/40 transition group">
            <div className="p-2.5 rounded-lg bg-cyan-950/60 text-cyan-400 w-fit mb-3 border border-cyan-800/60 group-hover:scale-110 transition-transform">
              <Code2 className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-100 mb-1">Zero-Boilerplate Testbenches</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Synthesizes asynchronous Python <code className="text-cyan-300 font-mono">cocotb</code> coroutines directly from RTL port ASTs without hundreds of lines of UVM boilerplate.
            </p>
          </div>

          <div className="p-5 rounded-xl border border-[#20304C] bg-[#0B111D]/80 backdrop-blur hover:border-purple-500/40 transition group">
            <div className="p-2.5 rounded-lg bg-purple-950/60 text-purple-400 w-fit mb-3 border border-purple-800/60 group-hover:scale-110 transition-transform">
              <Wrench className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-100 mb-1">Closed-Loop Self-Repair</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Simulator tracebacks and signal mismatches are translated into hardware diagnostics and iteratively patched until 100% test pass.
            </p>
          </div>

          <div className="p-5 rounded-xl border border-[#20304C] bg-[#0B111D]/80 backdrop-blur hover:border-amber-500/40 transition group">
            <div className="p-2.5 rounded-lg bg-amber-950/60 text-amber-400 w-fit mb-3 border border-amber-800/60 group-hover:scale-110 transition-transform">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-100 mb-1">Synthesizability First</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every verification cycle runs Yosys technology checks to prevent accidental combinational loops, multi-driven nets, and inferred latches.
            </p>
          </div>

          <div className="p-5 rounded-xl border border-[#20304C] bg-[#0B111D]/80 backdrop-blur hover:border-emerald-500/40 transition group">
            <div className="p-2.5 rounded-lg bg-emerald-950/60 text-emerald-400 w-fit mb-3 border border-emerald-800/60 group-hover:scale-110 transition-transform">
              <Clock className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-100 mb-1">STA & Timing Diagnostics</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Parses OpenROAD and OpenSTA logs to identify setup/hold slack violations and automatically suggests RTL pipelining diffs to close timing.
            </p>
          </div>

        </div>

        {/* Metrics Counter Bar */}
        <div className="mt-12 p-6 rounded-2xl border border-[#20304C] bg-[#10192A]/70 backdrop-blur grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          <div>
            <div className="text-2xl sm:text-3xl font-extrabold text-cyan-400 font-mono">99.4%</div>
            <div className="text-xs text-slate-400 mt-1 font-sans">Synthesizable RTL Pass Rate</div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-extrabold text-purple-400 font-mono">10x Faster</div>
            <div className="text-xs text-slate-400 mt-1 font-sans">Testbench Synthesis vs UVM</div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-extrabold text-amber-400 font-mono">4+ Simulators</div>
            <div className="text-xs text-slate-400 mt-1 font-sans">Icarus, Verilator, VCS, Xcelium</div>
          </div>
          <div>
            <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 font-mono">0 Boilerplate</div>
            <div className="text-xs text-slate-400 mt-1 font-sans">Native Python Async Coroutines</div>
          </div>
        </div>

      </div>
    </section>
  );
};
