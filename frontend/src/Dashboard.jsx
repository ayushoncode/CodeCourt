import React, { useState, useEffect, useRef } from 'react';
import { 
  Terminal, 
  Shield, 
  Activity, 
  Play, 
  RotateCcw, 
  Code, 
  Crosshair, 
  Zap, 
  CheckCircle2, 
  XCircle,
  Database
} from 'lucide-react';

const MOCK_PROBLEM = {
  title: "Dynamic Programming - Minimum Coins",
  constraints: "Time: 2.0s | Memory: 50MB | Complexity: O(N*C)",
  description: "Given a target amount and coin denominations, find the minimum number of coins to make the amount. Return -1 if impossible.",
  publicTests: 2,
  hiddenTests: 4,
  inputFormat: "First line: amount. Second line: space-separated coins.",
  outputFormat: "Minimum coins integer."
};

const MOCK_LOGS = [
  { type: "sys", text: "[SYS] Initializing Secure Sandbox Environment..." },
  { type: "sys", text: "[SYS] Compiling Blue Team Code (Python 3.11)..." },
  { type: "info", text: "[INFO] Compilation successful. Time: 0.12s" },
  { type: "test", text: "[TEST] Running Public Case 1... PASS (0.01s)" },
  { type: "test", text: "[TEST] Running Public Case 2... PASS (0.01s)" },
  { type: "warn", text: "[WARN] Initiating Adversarial Hidden Cases..." },
  { type: "test", text: "[TEST] Running Hidden Case 1 (Max Int)... PASS (0.04s)" },
  { type: "test", text: "[TEST] Running Hidden Case 2 (No Solution)... PASS (0.03s)" },
  { type: "test", text: "[TEST] Running Hidden Case 3 (Zero Amount)... PASS (0.01s)" },
  { type: "test", text: "[TEST] Running Hidden Case 4 (Adversarial Spread)... PASS (0.08s)" },
  { type: "oracle", text: "[ORACLE] Execution Complete. Analyzing Anti-Gaming Metrics..." },
  { type: "oracle", text: "[ORACLE] Memory Check: Peak 14.2MB (Under 50MB Limit)" },
  { type: "oracle", text: "[ORACLE] Complexity Check: Cyclomatic Complexity = 4 (Optimal)" },
];

export default function Dashboard() {
  // Global State Management
  const [activeEpisode, setActiveEpisode] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [executionStatus, setExecutionStatus] = useState("idle"); // "idle" | "running" | "completed"
  const [wsData, setWsData] = useState([]);
  
  // Form State
  const [archetype, setArchetype] = useState("Random");
  const [taskId, setTaskId] = useState(0);
  const [difficulty, setDifficulty] = useState(1);
  const [seed, setSeed] = useState(42);

  const logsEndRef = useRef(null);

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [wsData]);

  const handleCreateEpisode = () => {
    setIsLoading(true);
    setExecutionStatus("idle");
    setWsData([]);
    
    // Simulate network delay
    setTimeout(() => {
      setActiveEpisode({
        id: `ep_${Math.random().toString(36).substr(2, 6)}`,
        archetype,
        taskId,
        difficulty,
        seed,
        problem: MOCK_PROBLEM
      });
      setIsLoading(false);
    }, 1000);
  };

  const handleReset = () => {
    setActiveEpisode(null);
    setExecutionStatus("idle");
    setWsData([]);
    setIsLoading(false);
  };

  const runSolver = (mode) => {
    if (executionStatus === "running") return;
    
    setExecutionStatus("running");
    setWsData([]);

    let step = 0;
    const interval = setInterval(() => {
      if (step < MOCK_LOGS.length) {
        setWsData(prev => [...prev, MOCK_LOGS[step]]);
        step++;
      } else {
        clearInterval(interval);
        setExecutionStatus("completed");
      }
    }, 300); // Animate logs every 300ms
  };

  const LogLine = ({ log }) => {
    let colorClass = "text-gray-400";
    if (log.type === "sys") colorClass = "text-blue-400";
    if (log.type === "test") colorClass = log.text.includes("PASS") ? "text-emerald-400" : "text-rose-400";
    if (log.type === "warn") colorClass = "text-amber-400 font-bold";
    if (log.type === "oracle") colorClass = "text-purple-400";

    return <div className={`font-mono text-sm leading-relaxed ${colorClass}`}>{log.text}</div>;
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-200 font-sans selection:bg-blue-500/30">
      
      {/* Header */}
      <header className="sticky top-0 z-10 bg-gray-950/80 backdrop-blur-md border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Terminal className="w-6 h-6 text-blue-500" />
          <h1 className="text-xl font-bold tracking-tight text-white">CodeCourt <span className="text-gray-500 font-normal">//</span> Adversarial Arena</h1>
        </div>
        
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-4 text-sm font-medium">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <Crosshair className="w-4 h-4" />
              <span>Red Team Elo: 1000</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Shield className="w-4 h-4" />
              <span>Blue Team Elo: 1000</span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-full border border-emerald-400/20">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            WebSocket: Connected
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="p-6 grid grid-cols-12 gap-6 max-w-[1600px] mx-auto">
        
        {/* Left Panel: Interactive Console */}
        <div className="col-span-12 lg:col-span-3 space-y-6">
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
            <div className="flex items-center gap-2 mb-6">
              <Activity className="w-5 h-5 text-gray-400" />
              <h2 className="text-lg font-semibold text-white">Console Setup</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Archetype</label>
                <select 
                  value={archetype}
                  onChange={(e) => setArchetype(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                >
                  <option value="Random">Random</option>
                  <option value="Array">Array</option>
                  <option value="Graph">Graph</option>
                  <option value="DP">Dynamic Programming</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Task ID</label>
                  <input 
                    type="number" 
                    value={taskId}
                    onChange={(e) => setTaskId(Number(e.target.value))}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Difficulty</label>
                  <select 
                    value={difficulty}
                    onChange={(e) => setDifficulty(Number(e.target.value))}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  >
                    <option value={1}>Tier 1</option>
                    <option value={2}>Tier 2</option>
                    <option value={3}>Tier 3</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1.5">Seed</label>
                <input 
                  type="number" 
                  value={seed}
                  onChange={(e) => setSeed(Number(e.target.value))}
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>

              <div className="pt-4 flex gap-3">
                <button 
                  onClick={handleCreateEpisode}
                  disabled={isLoading}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-900/20"
                >
                  {isLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <Database className="w-4 h-4" />
                      Create Episode
                    </>
                  )}
                </button>
                <button 
                  onClick={handleReset}
                  className="p-2.5 text-gray-400 hover:text-white bg-gray-950 hover:bg-gray-800 border border-gray-800 rounded-lg transition-all"
                  title="Reset"
                >
                  <RotateCcw className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-5 shadow-lg backdrop-blur-sm">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">Execute Solvers</h3>
            <div className="space-y-3">
              <button 
                onClick={() => runSolver("baseline")}
                disabled={!activeEpisode || executionStatus === "running"}
                className="w-full bg-gray-800 hover:bg-gray-700 text-gray-200 font-medium py-2.5 px-4 rounded-lg flex items-center gap-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
              >
                <Play className="w-4 h-4 text-blue-400" />
                Run Baseline Blue Team
              </button>
              <button 
                onClick={() => runSolver("reference")}
                disabled={!activeEpisode || executionStatus === "running"}
                className="w-full bg-gray-800 hover:bg-gray-700 text-gray-200 font-medium py-2.5 px-4 rounded-lg flex items-center gap-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700"
              >
                <Zap className="w-4 h-4 text-amber-400" />
                Run Reference Blue Team
              </button>
              <button 
                onClick={() => runSolver("custom")}
                disabled={!activeEpisode || executionStatus === "running"}
                className="w-full bg-gray-950 hover:bg-gray-800 text-gray-400 hover:text-gray-200 font-medium py-2.5 px-4 rounded-lg flex items-center gap-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-gray-800 border-dashed"
              >
                <Code className="w-4 h-4" />
                Use Custom Code
              </button>
            </div>
          </div>
        </div>

        {/* Center Panel: Live Arena */}
        <div className="col-span-12 lg:col-span-9 flex flex-col gap-6">
          
          {!activeEpisode && !isLoading ? (
            <div className="flex-1 min-h-[600px] flex items-center justify-center bg-gray-900/30 border border-gray-800/50 border-dashed rounded-2xl">
              <div className="text-center space-y-4 max-w-sm">
                <div className="w-16 h-16 bg-gray-900 rounded-2xl flex items-center justify-center mx-auto border border-gray-800 shadow-xl">
                  <Terminal className="w-8 h-8 text-gray-600" />
                </div>
                <h3 className="text-xl font-medium text-gray-300">Awaiting Episode Creation</h3>
                <p className="text-gray-500 text-sm">Configure parameters on the left and click "Create Episode" to load an adversarial task.</p>
              </div>
            </div>
          ) : isLoading ? (
             <div className="flex-1 min-h-[600px] flex items-center justify-center bg-gray-900/30 border border-gray-800 rounded-2xl shadow-inner">
               <div className="flex flex-col items-center gap-4">
                 <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
                 <p className="text-gray-400 text-sm animate-pulse">Provisioning secure sandbox...</p>
               </div>
             </div>
          ) : (
            <>
              {/* Problem Definition Block */}
              <div className="bg-gray-900/80 border border-gray-800 rounded-xl overflow-hidden shadow-xl">
                <div className="bg-gray-950 px-5 py-3 border-b border-gray-800 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Code className="w-5 h-5 text-gray-400" />
                    <h2 className="font-medium text-gray-200">Current Problem: {activeEpisode.problem.title}</h2>
                  </div>
                  <div className="flex gap-2">
                    <span className="px-2.5 py-1 rounded bg-gray-800 text-gray-400 text-xs font-mono border border-gray-700">ID: {activeEpisode.id}</span>
                    <span className="px-2.5 py-1 rounded bg-purple-500/10 text-purple-400 text-xs font-mono border border-purple-500/20">{activeEpisode.problem.constraints}</span>
                  </div>
                </div>
                <div className="p-5">
                  <p className="text-gray-300 mb-6 leading-relaxed">{activeEpisode.problem.description}</p>
                  
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-gray-950 p-4 rounded-lg border border-gray-800/60">
                      <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Input Format</h4>
                      <div className="font-mono text-sm text-emerald-400">{activeEpisode.problem.inputFormat}</div>
                    </div>
                    <div className="bg-gray-950 p-4 rounded-lg border border-gray-800/60">
                      <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Output Format</h4>
                      <div className="font-mono text-sm text-blue-400">{activeEpisode.problem.outputFormat}</div>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <div className="flex items-center gap-2 text-sm text-gray-400 bg-gray-950 px-3 py-1.5 rounded-full border border-gray-800">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      Public Tests: {activeEpisode.problem.publicTests}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-400 bg-gray-950 px-3 py-1.5 rounded-full border border-gray-800">
                      <XCircle className="w-4 h-4 text-rose-500" />
                      Hidden Adversarial Tests: {activeEpisode.problem.hiddenTests}
                    </div>
                  </div>
                </div>
              </div>

              {/* WebSocket Spectator Terminal */}
              <div className="flex-1 bg-[#0a0a0f] border border-gray-800 rounded-xl overflow-hidden shadow-2xl flex flex-col relative">
                
                {/* Terminal Header */}
                <div className="bg-gray-900 px-4 py-2 border-b border-gray-800 flex items-center justify-between select-none">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1.5">
                      <div className="w-3 h-3 rounded-full bg-rose-500/20 border border-rose-500/50"></div>
                      <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500/50"></div>
                      <div className="w-3 h-3 rounded-full bg-emerald-500/20 border border-emerald-500/50"></div>
                    </div>
                    <span className="ml-2 text-xs font-mono text-gray-500">Live Execution Spectator</span>
                  </div>
                  {executionStatus === "running" && (
                    <div className="flex items-center gap-2 text-xs font-mono text-blue-400">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                      Executing...
                    </div>
                  )}
                </div>

                {/* Terminal Body */}
                <div className="flex-1 p-5 overflow-y-auto min-h-[300px]">
                  {executionStatus === "idle" ? (
                    <div className="h-full flex items-center justify-center text-gray-600 font-mono text-sm">
                      > Awaiting execution trigger...
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      {wsData.map((log, i) => (
                        <LogLine key={i} log={log} />
                      ))}
                      <div ref={logsEndRef} />
                    </div>
                  )}
                </div>

                {/* Final Metrics Banner */}
                {executionStatus === "completed" && (
                  <div className="absolute bottom-0 left-0 right-0 bg-blue-900/20 border-t border-blue-500/30 backdrop-blur-md p-4 animate-in slide-in-from-bottom-4 duration-500">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="bg-blue-500/20 p-2 rounded-lg border border-blue-500/30">
                          <CheckCircle2 className="w-6 h-6 text-blue-400" />
                        </div>
                        <div>
                          <h4 className="text-blue-100 font-medium">Solver Execution Complete</h4>
                          <p className="text-blue-300/80 text-sm">Passed all Red Team adversarial cases.</p>
                        </div>
                      </div>
                      
                      <div className="flex gap-6">
                        <div className="text-right">
                          <div className="text-xs text-blue-300/60 uppercase tracking-wider mb-1">Execution Time</div>
                          <div className="font-mono text-blue-200">0.14s <span className="text-emerald-400 ml-1">(+1.86 Bonus)</span></div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-blue-300/60 uppercase tracking-wider mb-1">Final Shaped Reward</div>
                          <div className="font-mono font-bold text-2xl text-emerald-400">+72.45</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
