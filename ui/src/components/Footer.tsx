import React from 'react';
import { Cpu, Github, ExternalLink, ArrowUp, ShieldCheck, Heart } from 'lucide-react';

interface FooterProps {
  onNavigate: (section: string) => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="bg-[#05080E] border-t border-[#20304C] pt-12 pb-8 text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          
          {/* Col 1: Brand & Mission */}
          <div className="space-y-3 md:col-span-1">
            <div className="flex items-center space-x-2">
              <div className="p-1.5 rounded bg-cyan-950 border border-cyan-500/40 text-cyan-400">
                <Cpu className="w-4 h-4" />
              </div>
              <span className="font-bold text-base text-slate-100 font-mono tracking-tight">EDA-Agent</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-xs">
              Autonomous Electronic Design Automation & VLSI Verification framework bridging SystemVerilog RTL with Python cocotb and closed-loop self-repair.
            </p>
            <div className="flex items-center space-x-2 text-[11px] font-mono text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Apache-2.0 Open Source</span>
            </div>
          </div>

          {/* Col 2: Navigation */}
          <div>
            <h4 className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider mb-3 text-cyan-400">
              Navigation
            </h4>
            <ul className="space-y-2 font-sans">
              <li>
                <button onClick={() => onNavigate('hero')} className="hover:text-cyan-300 transition">
                  Overview & Interactive Terminal
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('architecture')} className="hover:text-cyan-300 transition">
                  Multi-Stage Pipeline
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('field-guide')} className="hover:text-cyan-300 transition">
                  VLSI Field Guide & Case Studies
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('playground')} className="hover:text-cyan-300 transition">
                  Live Hardware Studio
                </button>
              </li>
            </ul>
          </div>

          {/* Col 3: Developer & Reference */}
          <div>
            <h4 className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider mb-3 text-purple-400">
              Developer Reference
            </h4>
            <ul className="space-y-2 font-sans">
              <li>
                <button onClick={() => onNavigate('cli')} className="hover:text-purple-300 transition">
                  CLI Reference & Generator
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('docs')} className="hover:text-purple-300 transition">
                  Python Core API Docs
                </button>
              </li>
              <li>
                <button onClick={() => onNavigate('roadmap')} className="hover:text-purple-300 transition">
                  Contributor & Roadmap Hub
                </button>
              </li>
              <li>
                <a
                  href="https://github.com/ashishsinghbora/eda-agent"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-purple-300 transition flex items-center space-x-1"
                >
                  <span>GitHub Repository</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
            </ul>
          </div>

          {/* Col 4: Ecosystem & Toolchains */}
          <div>
            <h4 className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider mb-3 text-emerald-400">
              Supported Toolchains
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {[
                'cocotb v2.0+',
                'Verilator 5.0+',
                'Yosys HQ',
                'Icarus Verilog',
                'OpenROAD / OpenSTA',
                'Ollama / vLLM',
                'Docker Compose',
                'SystemVerilog IEEE 1800'
              ].map((tool) => (
                <span
                  key={tool}
                  className="px-2 py-1 rounded text-[10px] font-mono bg-[#10192A] text-slate-300 border border-[#20304C]"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>

        </div>

        {/* Bottom copyright bar */}
        <div className="pt-6 border-t border-[#16233B] flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-[11px] text-slate-500 font-mono">
            © {new Date().getFullYear()} EDA-Agent. Built by{' '}
            <a
              href="https://github.com/ashishsinghbora"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:underline"
            >
              Ashish Singh Bora
            </a>
            . Licensed under Apache 2.0.
          </p>

          <button
            onClick={scrollToTop}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#10192A] hover:bg-[#16233B] text-slate-300 hover:text-cyan-300 border border-[#20304C] transition text-[11px] font-mono"
          >
            <span>Back to Top</span>
            <ArrowUp className="w-3.5 h-3.5" />
          </button>
        </div>

      </div>
    </footer>
  );
};
