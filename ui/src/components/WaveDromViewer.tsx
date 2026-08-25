import React, { useEffect, useRef } from 'react';
import { Activity, RefreshCw } from 'lucide-react';

interface WaveDromViewerProps {
  wavedromData: any;
  title?: string;
  className?: string;
}

declare global {
  interface Window {
    WaveDrom?: {
      ProcessAll: () => void;
      RenderWaveForm: (index: number, source: any, output: string) => void;
    };
  }
}

export const WaveDromViewer: React.FC<WaveDromViewerProps> = ({
  wavedromData,
  title = 'Digital Timing Waveform (VCD Extracted)',
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const waveId = useRef(`wave_${Math.random().toString(36).substring(2, 9)}`);

  useEffect(() => {
    if (!containerRef.current || !wavedromData) return;

    containerRef.current.innerHTML = '';
    const script = document.createElement('script');
    script.type = 'WaveDrom';
    script.text = JSON.stringify(wavedromData);
    containerRef.current.appendChild(script);

    if (window.WaveDrom && typeof window.WaveDrom.ProcessAll === 'function') {
      try {
        window.WaveDrom.ProcessAll();
      } catch (err) {
        console.warn('WaveDrom process error:', err);
      }
    }
  }, [wavedromData]);

  return (
    <div className={`rounded-lg border border-[#20304C] bg-[#0B111D] overflow-hidden shadow-xl ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-3.5 py-2 bg-[#10192A] border-b border-[#20304C] text-xs">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <span className="font-mono font-medium text-slate-200">{title}</span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
          VCD Live Stream
        </span>
      </div>

      {/* Waveform Output Container */}
      <div className="p-4 bg-[#070B12] overflow-x-auto min-h-[140px] flex items-center justify-center">
        <div
          ref={containerRef}
          id={waveId.current}
          className="w-full flex justify-center wavedrom-container"
        >
          {/* Fallback graphical indicator if waiting for script */}
          <div className="text-center py-6 text-slate-500 font-mono text-xs flex items-center space-x-2">
            <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
            <span>Rendering digital waveform traces...</span>
          </div>
        </div>
      </div>
    </div>
  );
};
