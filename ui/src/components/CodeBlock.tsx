import React, { useState, useEffect, useRef } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-verilog';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import { Copy, Check, Terminal, FileCode, Code2 } from 'lucide-react';

interface CodeBlockProps {
  code: string;
  language?: 'verilog' | 'python' | 'bash' | 'json' | 'systemverilog' | 'text';
  filename?: string;
  showLineNumbers?: boolean;
  maxHeight?: string;
  className?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'verilog',
  filename,
  showLineNumbers = true,
  maxHeight = '420px',
  className = '',
}) => {
  const [copied, setCopied] = useState(false);
  const codeRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (codeRef.current) {
      Prism.highlightElement(codeRef.current);
    }
  }, [code, language]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code: ', err);
    }
  };

  const getLanguageIcon = () => {
    if (language === 'bash') return <Terminal className="w-3.5 h-3.5 text-cyan-400" />;
    if (language === 'python') return <Code2 className="w-3.5 h-3.5 text-emerald-400" />;
    return <FileCode className="w-3.5 h-3.5 text-purple-400" />;
  };

  const getLanguageLabel = () => {
    switch (language) {
      case 'verilog':
      case 'systemverilog':
        return 'SystemVerilog';
      case 'python':
        return 'Python (cocotb)';
      case 'bash':
        return 'Bash CLI';
      case 'json':
        return 'JSON Schema';
      default:
        return language.toUpperCase();
    }
  };

  const prismLang = language === 'systemverilog' ? 'verilog' : language;

  return (
    <div className={`rounded-lg border border-[#20304C] bg-[#0B111D] overflow-hidden shadow-xl ${className}`}>
      {/* Header bar */}
      <div className="flex items-center justify-between px-3.5 py-2 bg-[#10192A] border-b border-[#20304C] text-xs">
        <div className="flex items-center space-x-2">
          {getLanguageIcon()}
          {filename ? (
            <span className="font-mono font-medium text-slate-200">{filename}</span>
          ) : (
            <span className="font-mono text-slate-400 text-[11px]">{getLanguageLabel()}</span>
          )}
          {filename && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
              {getLanguageLabel()}
            </span>
          )}
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#16233B] hover:bg-[#20304C] text-slate-300 hover:text-cyan-300 border border-[#20304C] transition text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-cyan-400"
          title="Copy code to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-semibold">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-slate-400" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Container */}
      <div
        className="p-4 overflow-auto font-mono text-xs leading-relaxed bg-[#070B12]"
        style={{ maxHeight }}
      >
        <pre className={`language-${prismLang} ${showLineNumbers ? 'line-numbers' : ''} m-0 p-0`}>
          <code ref={codeRef} className={`language-${prismLang}`}>
            {code.trim()}
          </code>
        </pre>
      </div>
    </div>
  );
};
