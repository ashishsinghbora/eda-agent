export interface Port {
  name: string;
  direction: 'input' | 'output' | 'inout';
  width: string;
  is_clock: boolean;
  is_reset: boolean;
  type?: string;
}

export interface ModuleSpec {
  name: string;
  ports: Port[];
  parameters: { [key: string]: string };
  fsm_states?: string[];
  clock_domain?: string;
  description?: string;
}

export interface PipelineStage {
  id: string;
  title: string;
  subtitle: string;
  iconName: string;
  modulePath: string;
  description: string;
  inputs: string[];
  outputs: string[];
  toolCommand: string;
  sampleDiagnostic: string;
  recoveryAction: string;
  color: 'cyan' | 'purple' | 'emerald' | 'amber' | 'rose' | 'blue';
}

export interface CaseStudy {
  id: string;
  title: string;
  category: 'FSM Deadlock' | 'Combinational Latch' | 'CDC Metastability' | 'STA Negative Slack';
  severity: 'Critical' | 'High' | 'Medium';
  badRTL: string;
  goodRTL: string;
  explanation: string;
  agentDiagnostic: string;
  testbenchSnippet: string;
  timingWaveform?: any;
}

export interface CliCommand {
  name: string;
  syntax: string;
  description: string;
  category: 'Core Flow' | 'Diagnostics & STA' | 'Assertions' | 'Configuration & UI';
  flags: {
    flag: string;
    description: string;
    default?: string;
    required?: boolean;
  }[];
  sampleExecution: string;
  sampleOutput: string;
}

export interface ApiDocSection {
  package: string;
  title: string;
  description: string;
  classes: {
    name: string;
    summary: string;
    methods: {
      signature: string;
      description: string;
      returnType: string;
    }[];
    exampleCode: string;
  }[];
}

export interface HardwarePreset {
  id: string;
  name: string;
  filename: string;
  category: string;
  description: string;
  specPreset: string;
  code: string;
  moduleSpec: ModuleSpec;
  testbench: string;
  sva: string;
  wavedrom: any;
  simLog: string;
}
