import React, { useState, useEffect } from 'react';
import { Search, X, Terminal, Cpu, BookOpen, Layers, Code, ArrowRight } from 'lucide-react';
import { cliCommands } from '../data/cliData';
import { pipelineStages } from '../data/architectureData';
import { fieldCaseStudies } from '../data/fieldGuideData';
import { apiDocs } from '../data/docsData';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (sectionId: string, itemKey?: string) => void;
}

interface SearchItem {
  id: string;
  category: 'CLI Command' | 'Pipeline Stage' | 'Field Guide Case Study' | 'Python API';
  title: string;
  subtitle: string;
  sectionId: string;
  itemKey?: string;
  icon: any;
}

export const SearchModal: React.FC<SearchModalProps> = ({
  isOpen,
  onClose,
  onNavigate,
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Compile searchable corpus
  const allItems: SearchItem[] = [
    // CLI commands
    ...cliCommands.map((cmd) => ({
      id: `cli_${cmd.name}`,
      category: 'CLI Command' as const,
      title: `eda-agent ${cmd.name}`,
      subtitle: cmd.description,
      sectionId: 'cli',
      itemKey: cmd.name,
      icon: Terminal,
    })),
    // Architecture stages
    ...pipelineStages.map((stage) => ({
      id: `arch_${stage.id}`,
      category: 'Pipeline Stage' as const,
      title: stage.title,
      subtitle: stage.subtitle,
      sectionId: 'architecture',
      itemKey: stage.id,
      icon: Layers,
    })),
    // Case Studies
    ...fieldCaseStudies.map((study) => ({
      id: `case_${study.id}`,
      category: 'Field Guide Case Study' as const,
      title: study.title,
      subtitle: study.explanation.substring(0, 100) + '...',
      sectionId: 'field-guide',
      itemKey: study.id,
      icon: BookOpen,
    })),
    // API Docs
    ...apiDocs.flatMap((pkg) =>
      pkg.classes.map((cls) => ({
        id: `api_${cls.name}`,
        category: 'Python API' as const,
        title: `${pkg.package}.${cls.name}`,
        subtitle: cls.summary,
        sectionId: 'docs',
        itemKey: cls.name,
        icon: Code,
      }))
    ),
  ];

  const filteredItems = query.trim() === ''
    ? allItems.slice(0, 7)
    : allItems.filter(
        (item) =>
          item.title.toLowerCase().includes(query.toLowerCase()) ||
          item.subtitle.toLowerCase().includes(query.toLowerCase()) ||
          item.category.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 12);

  // Keyboard navigation inside modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % (filteredItems.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % (filteredItems.length || 1));
      } else if (e.key === 'Enter' && filteredItems[selectedIndex]) {
        e.preventDefault();
        const selected = filteredItems[selectedIndex];
        onNavigate(selected.sectionId, selected.itemKey);
        onClose();
      } else if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredItems, selectedIndex, onNavigate, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-150">
      <div
        className="w-full max-w-2xl bg-[#0B111D] border border-[#20304C] rounded-xl shadow-2xl overflow-hidden glass-panel-glow"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-[#20304C] bg-[#10192A]">
          <Search className="w-5 h-5 text-cyan-400 mr-3 shrink-0" />
          <input
            type="text"
            placeholder="Search CLI commands, architecture stages, API classes, case studies... (Esc to close)"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            autoFocus
            className="w-full bg-transparent text-slate-100 placeholder-slate-500 font-mono text-sm focus:outline-none"
          />
          {query && (
            <button onClick={() => setQuery('')} className="p-1 text-slate-400 hover:text-slate-200">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Results List */}
        <div className="max-h-[380px] overflow-y-auto p-2 divide-y divide-[#16233B]">
          {filteredItems.length === 0 ? (
            <div className="py-12 text-center text-slate-500 font-mono text-xs">
              No matching commands, API symbols, or documentation found.
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => {
                    onNavigate(item.sectionId, item.itemKey);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition ${
                    isSelected
                      ? 'bg-[#16233B] border border-cyan-500/40 text-cyan-300'
                      : 'hover:bg-[#10192A] text-slate-300'
                  }`}
                >
                  <div className="flex items-start space-x-3 overflow-hidden">
                    <div
                      className={`p-2 rounded-md shrink-0 ${
                        isSelected ? 'bg-cyan-950 text-cyan-400' : 'bg-[#10192A] text-slate-400'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="overflow-hidden">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-sm font-semibold truncate text-slate-100">
                          {item.title}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-[#10192A] text-slate-400 border border-[#20304C]">
                          {item.category}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 font-sans truncate mt-0.5">
                        {item.subtitle}
                      </p>
                    </div>
                  </div>
                  <ArrowRight
                    className={`w-4 h-4 shrink-0 transition ${
                      isSelected ? 'text-cyan-400 translate-x-1' : 'text-slate-600'
                    }`}
                  />
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2.5 bg-[#070B12] border-t border-[#20304C] flex items-center justify-between text-[11px] font-mono text-slate-500">
          <div className="flex items-center space-x-3">
            <span><kbd className="px-1.5 py-0.5 rounded bg-[#16233B] text-slate-300 border border-[#20304C]">↑</kbd> <kbd className="px-1.5 py-0.5 rounded bg-[#16233B] text-slate-300 border border-[#20304C]">↓</kbd> to navigate</span>
            <span><kbd className="px-1.5 py-0.5 rounded bg-[#16233B] text-slate-300 border border-[#20304C]">↵</kbd> to select</span>
          </div>
          <span><kbd className="px-1.5 py-0.5 rounded bg-[#16233B] text-slate-300 border border-[#20304C]">ESC</kbd> to close</span>
        </div>
      </div>
    </div>
  );
};
