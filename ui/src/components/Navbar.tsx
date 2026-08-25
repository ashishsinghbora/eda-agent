import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Layers, 
  BookOpen, 
  Terminal, 
  Code2, 
  GitFork, 
  Star, 
  Search, 
  Menu, 
  X, 
  FlaskConical, 
  Sparkles, 
  ExternalLink 
} from 'lucide-react';

interface NavbarProps {
  activeSection: string;
  onNavigate: (section: string) => void;
  onOpenSearch: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeSection,
  onNavigate,
  onOpenSearch,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { id: 'hero', label: 'Overview', icon: Sparkles },
    { id: 'architecture', label: 'Architecture', icon: Layers },
    { id: 'field-guide', label: 'Field Guide', icon: BookOpen },
    { id: 'playground', label: 'Live Studio', icon: FlaskConical },
    { id: 'cli', label: 'Quickstart & CLI', icon: Terminal },
    { id: 'docs', label: 'API Reference', icon: Code2 },
    { id: 'roadmap', label: 'Roadmap & PRs', icon: GitFork },
  ];

  const handleNavClick = (id: string) => {
    onNavigate(id);
    setMobileMenuOpen(false);
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
        scrolled
          ? 'bg-[#070B12]/90 backdrop-blur-md border-b border-[#20304C]/80 shadow-2xl py-2.5'
          : 'bg-[#070B12]/60 backdrop-blur-sm border-b border-[#20304C]/40 py-3.5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        
        {/* Brand Logo */}
        <div 
          onClick={() => handleNavClick('hero')}
          className="flex items-center space-x-3 cursor-pointer group select-none"
        >
          <div className="relative p-2 rounded-lg bg-gradient-to-br from-cyan-500/20 to-purple-600/20 border border-cyan-500/40 group-hover:border-cyan-400 transition-all shadow-[0_0_15px_rgba(0,240,255,0.2)]">
            <Cpu className="w-5 h-5 text-cyan-400 group-hover:rotate-12 transition-transform duration-300" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping opacity-75"></span>
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-cyan-400 via-teal-300 to-purple-400 bg-clip-text text-transparent">
                EDA-Agent
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/80 font-semibold shadow-sm">
                v0.1.0
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono hidden sm:block">
              Autonomous VLSI Verification & Self-Repair
            </span>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center space-x-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium font-sans transition-all ${
                  isActive
                    ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(0,240,255,0.15)]'
                    : 'text-slate-300 hover:text-cyan-300 hover:bg-[#10192A]'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right Actions: Search + GitHub */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          
          {/* Quick Search trigger button */}
          <button
            onClick={onOpenSearch}
            className="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg bg-[#10192A] hover:bg-[#16233B] text-slate-400 hover:text-slate-200 border border-[#20304C] text-xs font-mono transition"
            title="Search docs and commands (Cmd+K)"
          >
            <Search className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden md:inline text-[11px]">Search</span>
            <kbd className="hidden md:inline px-1.5 py-0.2 rounded bg-[#0B111D] text-[10px] text-slate-400 border border-[#20304C]">
              ⌘K
            </kbd>
          </button>

          {/* GitHub Star button */}
          <a
            href="https://github.com/ashishsinghbora/eda-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#10192A] to-[#16233B] hover:from-cyan-950 hover:to-purple-950 text-slate-200 hover:text-cyan-200 border border-[#20304C] hover:border-cyan-500/50 text-xs font-mono transition-all shadow-md group"
          >
            <Star className="w-3.5 h-3.5 text-amber-400 group-hover:scale-110 transition-transform" />
            <span className="font-semibold">Star</span>
            <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-cyan-400" />
          </a>

          {/* Mobile hamburger button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-lg bg-[#10192A] text-slate-300 hover:text-white border border-[#20304C]"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

        </div>

      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-[#0B111D] border-b border-[#20304C] px-4 pt-3 pb-5 space-y-1.5 animate-in slide-in-from-top-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-500/50'
                    : 'text-slate-300 hover:bg-[#10192A]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};
