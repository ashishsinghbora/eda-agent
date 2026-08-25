import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { ArchitectureVisualizer } from './components/ArchitectureVisualizer';
import { FieldGuideSection } from './components/FieldGuideSection';
import { HardwareStudio } from './components/HardwareStudio';
import { CliQuickstartSection } from './components/CliQuickstartSection';
import { DocsApiSection } from './components/DocsApiSection';
import { ContributorRoadmapSection } from './components/ContributorRoadmapSection';
import { Footer } from './components/Footer';
import { SearchModal } from './components/SearchModal';

export const App: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string>('hero');
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);

  // Global Cmd+K / Ctrl+K shortcut to open search modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Track active section on scroll
  useEffect(() => {
    const sectionIds = ['hero', 'architecture', 'field-guide', 'playground', 'cli', 'docs', 'roadmap'];
    
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 200;
      for (const id of sectionIds) {
        const el = document.getElementById(id);
        if (el) {
          const top = el.offsetTop;
          const height = el.offsetHeight;
          if (scrollPosition >= top && scrollPosition < top + height) {
            setActiveSection(id);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavigate = (sectionId: string, itemKey?: string) => {
    setActiveSection(sectionId);
    const targetElement = document.getElementById(sectionId);
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#070B12] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200">
      
      {/* Navigation Bar */}
      <Navbar
        activeSection={activeSection}
        onNavigate={handleNavigate}
        onOpenSearch={() => setIsSearchOpen(true)}
      />

      {/* Main Content Sections */}
      <main>
        <div id="hero">
          <HeroSection onNavigate={handleNavigate} />
        </div>

        <div id="architecture">
          <ArchitectureVisualizer />
        </div>

        <div id="field-guide">
          <FieldGuideSection />
        </div>

        <div id="playground">
          <HardwareStudio />
        </div>

        <div id="cli">
          <CliQuickstartSection />
        </div>

        <div id="docs">
          <DocsApiSection />
        </div>

        <div id="roadmap">
          <ContributorRoadmapSection />
        </div>
      </main>

      {/* Footer */}
      <Footer onNavigate={handleNavigate} />

      {/* Global Command Palette / Search Modal */}
      <SearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onNavigate={handleNavigate}
      />

    </div>
  );
};

export default App;
