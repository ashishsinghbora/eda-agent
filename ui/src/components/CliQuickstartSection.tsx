import React, { useState } from 'react';
import { 
  Terminal, 
  Copy, 
  Check, 
  Cpu, 
  Container, 
  Code, 
  Layers, 
  Sparkles, 
  Play, 
  Settings, 
  ExternalLink,
  ChevronDown,
  Info
} from 'lucide-react';
import { CodeBlock } from './CodeBlock';
import { cliCommands } from '../data/cliData';

export const CliQuickstartSection: React.FC = () => {
  const [setupTab, setSetupTab] = useState<'docker' | 'venv' | 'binaries'>('docker');
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  // CLI Generator State
  const [selectedSubcmd, setSelectedSubcmd] = useState<string>('verify');
  const [targetRtl, setTargetRtl] = useState<string>('examples/rtl/alu_8bit.v');
  const [maxRetries, setMaxRetries] = useState<string>('3');
  const [simulator, setSimulator] = useState<string>('icarus');
  const [dumpVcd, setDumpVcd] = useState<boolean>(true);
  const [jsonOutput, setJsonOutput] = useState<boolean>(false);
  const [nlSpec, setNlSpec] = useState<string>('');
  const [llmProvider, setLlmProvider] = useState<string>('ollama');
  const [llmModel, setLlmModel] = useState<string>('deepseek-coder-v2:16b');

  const handleCopyText = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCmd(id);
      setTimeout(() => setCopiedCmd(null), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  // Build dynamic generated CLI command string
  const buildGeneratedCommand = () => {
    let cmd = `eda-agent ${selectedSubcmd}`;
    if (['verify', 'lint', 'synth', 'generate', 'assert'].includes(selectedSubcmd)) {
      cmd += ` ${targetRtl}`;
    }

    if (selectedSubcmd === 'verify') {
      if (maxRetries !== '3') cmd += ` --max-retries ${maxRetries}`;
      if (simulator !== 'icarus') cmd += ` --simulator ${simulator}`;
      if (dumpVcd) cmd += ` --dump-vcd`;
      if (nlSpec) cmd += ` --spec "${nlSpec}"`;
    } else if (selectedSubcmd === 'lint') {
      if (jsonOutput) cmd += ` --json-output`;
    } else if (selectedSubcmd === 'assert') {
      cmd += ` -s "${nlSpec || 'ready drops low when full'}"`;
    } else if (selectedSubcmd === 'config') {
      cmd += ` --provider ${llmProvider} --model ${llmModel}`;
    } else if (selectedSubcmd === 'triage-log') {
      cmd = `eda-agent triage-log sim.log --rtl ${targetRtl}`;
    } else if (selectedSubcmd === 'analyze-timing') {
      cmd = `eda-agent analyze-timing examples/logs/openroad_sta_violated.log --suggest-pipeline`;
    }

    return cmd;
  };

  const generatedCommand = buildGeneratedCommand();
  const currentCliDoc = cliCommands.find((c) => c.name === selectedSubcmd) || cliCommands[0];

  return (
    <section id="cli" className="py-20 bg-[#0B111D] border-t border-[#20304C] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#10192A] border border-cyan-500/30 text-cyan-300 text-xs font-mono mb-3">
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            <span>Quickstart & Command Line Suite</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
            Installation & Interactive CLI Generator
          </h2>
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            Get up and running in seconds with zero host dependencies using Docker, or configure bare-metal binaries and generate real-time CLI commands.
          </p>
        </div>

        {/* SECTION 1: INSTALLATION TABS */}
        <div className="rounded-2xl border border-[#20304C] bg-[#070B12] overflow-hidden shadow-2xl mb-16">
          
          {/* Tabs header */}
          <div className="flex border-b border-[#20304C] bg-[#10192A] overflow-x-auto">
            <button
              onClick={() => setSetupTab('docker')}
              className={`flex items-center space-x-2 px-6 py-3.5 text-xs font-mono transition border-b-2 ${
                setupTab === 'docker'
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-950/40 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Container className="w-4 h-4 text-cyan-400" />
              <span>Option A: Zero-Dependency Docker (Recommended)</span>
            </button>

            <button
              onClick={() => setSetupTab('venv')}
              className={`flex items-center space-x-2 px-6 py-3.5 text-xs font-mono transition border-b-2 ${
                setupTab === 'venv'
                  ? 'border-purple-400 text-purple-300 bg-purple-950/40 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code className="w-4 h-4 text-purple-400" />
              <span>Option B: Local Python Virtualenv</span>
            </button>

            <button
              onClick={() => setSetupTab('binaries')}
              className={`flex items-center space-x-2 px-6 py-3.5 text-xs font-mono transition border-b-2 ${
                setupTab === 'binaries'
                  ? 'border-emerald-400 text-emerald-300 bg-emerald-950/40 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Cpu className="w-4 h-4 text-emerald-400" />
              <span>Option C: Native EDA Binaries (Verilator / Yosys)</span>
            </button>
          </div>

          {/* Tab content */}
          <div className="p-6">
            {setupTab === 'docker' && (
              <div className="space-y-4">
                <p className="text-xs text-slate-300">
                  Run the complete containerized EDA environment (Verilator, Icarus, Yosys, FastAPI, and Web Studio) with zero manual host configuration:
                </p>
                <CodeBlock
                  code={`# 1. Clone the open-source repository
git clone https://github.com/ashishsinghbora/eda-agent.git
cd eda-agent

# 2. Launch containerized Web Studio and API service
docker compose up -d

# 3. Access Web Studio in your browser
open http://localhost:8000

# 4. Run verification CLI directly inside Docker
docker compose run --rm eda-agent verify examples/rtl/alu_8bit.v`}
                  language="bash"
                  filename="terminal"
                />
              </div>
            )}

            {setupTab === 'venv' && (
              <div className="space-y-4">
                <p className="text-xs text-slate-300">
                  Install EDA-Agent into a local Python 3.11+ virtual environment:
                </p>
                <CodeBlock
                  code={`# 1. Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install EDA-Agent in editable mode with all dependencies
pip install -e .

# 3. Verify toolchain installation
eda-agent info`}
                  language="bash"
                  filename="terminal"
                />
              </div>
            )}

            {setupTab === 'binaries' && (
              <div className="space-y-4">
                <p className="text-xs text-slate-300">
                  Install open-source EDA compilers on your operating system:
                </p>
                <CodeBlock
                  code={`# Ubuntu / Debian
sudo apt-get update && sudo apt-get install -y iverilog verilator yosys build-essential make

# Arch Linux
sudo pacman -S iverilog verilator yosys make

# Fedora / RHEL
sudo dnf install -y iverilog verilator yosys make

# macOS (Homebrew)
brew install icarus-verilog verilator yosys make`}
                  language="bash"
                  filename="terminal"
                />
              </div>
            )}
          </div>

        </div>

        {/* SECTION 2: INTERACTIVE CLI COMMAND GENERATOR */}
        <div className="rounded-2xl border border-[#20304C] bg-[#070B12] overflow-hidden shadow-2xl mb-16">
          
          <div className="px-6 py-4 bg-[#10192A] border-b border-[#20304C] flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-slate-100 font-mono flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span>Interactive CLI Command Generator</span>
              </h3>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                Toggle options below to generate exact bash commands and preview simulated output.
              </p>
            </div>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
              Interactive Builder
            </span>
          </div>

          <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left: Options Controls (5 cols) */}
            <div className="lg:col-span-5 space-y-4 bg-[#0B111D] p-5 rounded-xl border border-[#20304C]">
              
              {/* Subcommand selector */}
              <div>
                <label className="text-xs font-bold font-mono text-slate-300 uppercase block mb-1.5">
                  Subcommand
                </label>
                <select
                  value={selectedSubcmd}
                  onChange={(e) => setSelectedSubcmd(e.target.value)}
                  className="w-full bg-[#070B12] border border-[#20304C] rounded-lg p-2 text-xs text-cyan-300 font-mono focus:outline-none focus:border-cyan-400"
                >
                  {cliCommands.map((cmd) => (
                    <option key={cmd.name} value={cmd.name}>
                      eda-agent {cmd.name} — {cmd.description.substring(0, 45)}...
                    </option>
                  ))}
                </select>
              </div>

              {/* Target RTL File */}
              {['verify', 'lint', 'synth', 'generate', 'assert', 'triage-log'].includes(selectedSubcmd) && (
                <div>
                  <label className="text-xs font-bold font-mono text-slate-300 uppercase block mb-1.5">
                    Target RTL Path
                  </label>
                  <input
                    type="text"
                    value={targetRtl}
                    onChange={(e) => setTargetRtl(e.target.value)}
                    className="w-full bg-[#070B12] border border-[#20304C] rounded-lg p-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                  />
                </div>
              )}

              {/* Conditional Flags */}
              {selectedSubcmd === 'verify' && (
                <div className="space-y-3 pt-2 border-t border-[#16233B]">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[11px] font-mono text-slate-400 block mb-1">Max Retries</label>
                      <select
                        value={maxRetries}
                        onChange={(e) => setMaxRetries(e.target.value)}
                        className="w-full bg-[#070B12] border border-[#20304C] rounded p-1.5 text-xs text-slate-200 font-mono"
                      >
                        <option value="1">1 attempt</option>
                        <option value="3">3 attempts (default)</option>
                        <option value="5">5 attempts</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[11px] font-mono text-slate-400 block mb-1">Simulator</label>
                      <select
                        value={simulator}
                        onChange={(e) => setSimulator(e.target.value)}
                        className="w-full bg-[#070B12] border border-[#20304C] rounded p-1.5 text-xs text-slate-200 font-mono"
                      >
                        <option value="icarus">Icarus Verilog</option>
                        <option value="verilator">Verilator C++</option>
                        <option value="vcs">Synopsys VCS</option>
                      </select>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 pt-1">
                    <input
                      type="checkbox"
                      id="vcd_check"
                      checked={dumpVcd}
                      onChange={(e) => setDumpVcd(e.target.checked)}
                      className="rounded border-[#20304C] bg-[#070B12] text-cyan-500 focus:ring-0"
                    />
                    <label htmlFor="vcd_check" className="text-xs font-mono text-slate-300">
                      Generate VCD Waveforms (--dump-vcd)
                    </label>
                  </div>
                </div>
              )}

              {selectedSubcmd === 'lint' && (
                <div className="pt-2 border-t border-[#16233B]">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="json_check"
                      checked={jsonOutput}
                      onChange={(e) => setJsonOutput(e.target.checked)}
                      className="rounded border-[#20304C] bg-[#070B12] text-cyan-500"
                    />
                    <label htmlFor="json_check" className="text-xs font-mono text-slate-300">
                      Output Structured JSON (--json-output)
                    </label>
                  </div>
                </div>
              )}

              {selectedSubcmd === 'config' && (
                <div className="space-y-3 pt-2 border-t border-[#16233B]">
                  <div>
                    <label className="text-[11px] font-mono text-slate-400 block mb-1">LLM Provider</label>
                    <select
                      value={llmProvider}
                      onChange={(e) => setLlmProvider(e.target.value)}
                      className="w-full bg-[#070B12] border border-[#20304C] rounded p-1.5 text-xs text-slate-200 font-mono"
                    >
                      <option value="ollama">Ollama (Local Airgapped)</option>
                      <option value="openai_compatible">vLLM / Local Endpoint</option>
                      <option value="gemini">Google Gemini</option>
                      <option value="openai">OpenAI</option>
                      <option value="rule_based">Rule Engine (No LLM)</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[11px] font-mono text-slate-400 block mb-1">Model Name</label>
                    <input
                      type="text"
                      value={llmModel}
                      onChange={(e) => setLlmModel(e.target.value)}
                      className="w-full bg-[#070B12] border border-[#20304C] rounded p-1.5 text-xs text-slate-200 font-mono"
                    />
                  </div>
                </div>
              )}

            </div>

            {/* Right: Generated Command & Simulated Terminal (7 cols) */}
            <div className="lg:col-span-7 flex flex-col space-y-4">
              
              {/* Generated command display box */}
              <div className="p-4 rounded-xl bg-[#10192A] border border-cyan-500/40 flex items-center justify-between">
                <div className="overflow-x-auto mr-3">
                  <div className="text-[10px] font-mono text-cyan-400 uppercase font-bold mb-1">
                    Generated Bash Command:
                  </div>
                  <code className="text-xs font-mono text-slate-100 font-bold whitespace-nowrap">
                    {generatedCommand}
                  </code>
                </div>

                <button
                  onClick={() => handleCopyText(generatedCommand, 'gen_cmd')}
                  className="px-3 py-1.5 rounded-lg bg-[#070B12] hover:bg-[#16233B] text-cyan-300 border border-[#20304C] transition text-xs font-mono shrink-0 flex items-center space-x-1.5"
                >
                  {copiedCmd === 'gen_cmd' ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>

              {/* Simulated Output Box */}
              <div>
                <div className="text-xs font-bold font-mono text-slate-400 mb-1.5 flex items-center space-x-1.5">
                  <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Expected Terminal Output:</span>
                </div>
                <div className="p-4 rounded-xl bg-[#070B12] border border-[#20304C] font-mono text-xs text-slate-300 max-h-[280px] overflow-y-auto leading-relaxed whitespace-pre-wrap">
                  {currentCliDoc.sampleOutput}
                </div>
              </div>

            </div>

          </div>

        </div>

        {/* SECTION 3: FULL CLI REFERENCE TABLE */}
        <div className="rounded-2xl border border-[#20304C] bg-[#070B12] overflow-hidden shadow-xl">
          <div className="px-6 py-4 bg-[#10192A] border-b border-[#20304C]">
            <h3 className="text-base font-bold text-slate-100 font-mono">
              Complete CLI Command & Option Reference
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#0B111D] border-b border-[#20304C] text-slate-400 uppercase text-[11px]">
                <tr>
                  <th className="py-3.5 px-6">Command</th>
                  <th className="py-3.5 px-6">Category</th>
                  <th className="py-3.5 px-6">Description</th>
                  <th className="py-3.5 px-6">Example Syntax</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#16233B]">
                {cliCommands.map((cmd) => (
                  <tr key={cmd.name} className="hover:bg-[#10192A]/50 transition">
                    <td className="py-3.5 px-6 font-bold text-cyan-300">
                      eda-agent {cmd.name}
                    </td>
                    <td className="py-3.5 px-6">
                      <span className="text-[10px] px-2 py-0.5 rounded bg-[#10192A] text-purple-300 border border-[#20304C]">
                        {cmd.category}
                      </span>
                    </td>
                    <td className="py-3.5 px-6 text-slate-300 font-sans">
                      {cmd.description}
                    </td>
                    <td className="py-3.5 px-6 text-amber-300 font-mono text-[11px]">
                      {cmd.syntax}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </section>
  );
};
