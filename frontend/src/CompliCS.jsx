import { useState, useRef, useEffect } from "react";
import {
  Scale,
  BookOpen,
  Cpu,
  Search,
  ChevronRight,
  Shield,
  Zap,
  FileText,
  Copy,
  CheckCheck,
  ArrowRight,
  Layers,
  Database,
  Sparkles,
  MessageSquare,
  AlertCircle,
  ChevronDown,
  Plus,
  Clock,
  Users,
  Briefcase,
  GraduationCap,
  Building2,
  SendHorizontal,
  PanelRight,
  Menu,
  X,
  CircleDot,
  Hash,
  CornerDownLeft,
} from "lucide-react";

const API_URL = "http://localhost:8000";

const QUICK_ACTIONS = [
  {
    icon: AlertCircle,
    label: "Director Disqualification",
    query: "What are the grounds for director disqualification under Section 164 of the Companies Act 2013?",
  },
  {
    icon: FileText,
    label: "LLP Incorporation",
    query: "What is the procedure and timeline for incorporating an LLP under the LLP Act 2008?",
  },
  {
    icon: Clock,
    label: "Sectional Query",
    query: "What does Section 173 state regarding board meetings?",
  },
  {
    icon: Shield,
    label: "CSR Obligations",
    query: "Which companies are required to comply with CSR provisions under Section 135 and what are the penalties for non-compliance?",
  },
];

function MarkdownRenderer({ content }) {
  // Pre-process: strip code fences and control tokens that may leak from the LLM
  let cleaned = content.replace(/```[\s\S]*?```/g, '').replace(/```/g, '');
  // Strip Mistral control tokens
  cleaned = cleaned.replace(/\[control_\d+\]/g, '').replace(/\[\/?[A-Z_]{2,}\]/g, '');
  // Clean up excessive whitespace
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n');
  const lines = cleaned.split("\n");
  const elements = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith("## ")) {
      elements.push(
        <h2 key={i} style={{ fontSize: "15px", fontWeight: 600, color: "#f1f5f9", marginTop: "1.25rem", marginBottom: "0.5rem", letterSpacing: "-0.01em" }}>
          {line.replace("## ", "")}
        </h2>
      );
    } else if (line.startsWith("### ")) {
      elements.push(
        <h3 key={i} style={{ fontSize: "13px", fontWeight: 600, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.06em", marginTop: "1rem", marginBottom: "0.4rem" }}>
          {line.replace("### ", "")}
        </h3>
      );
    } else if (line.startsWith("> ")) {
      elements.push(
        <blockquote key={i} style={{ borderLeft: "3px solid #10b981", paddingLeft: "1rem", margin: "0.75rem 0", color: "#94a3b8", fontSize: "13px", fontStyle: "italic", background: "rgba(16,185,129,0.04)", borderRadius: "0 6px 6px 0", padding: "0.6rem 1rem" }}>
          {line.replace("> ", "")}
        </blockquote>
      );
    } else if (/^\d+\. /.test(line)) {
      const items = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\. /, ""));
        i++;
      }
      elements.push(
        <ol key={`ol-${i}`} style={{ paddingLeft: "1.25rem", margin: "0.5rem 0", color: "#cbd5e1", fontSize: "13.5px", lineHeight: 1.75 }}>
          {items.map((item, j) => (
            <li key={j} dangerouslySetInnerHTML={{ __html: item.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#f1f5f9;font-weight:600">$1</strong>') }} />
          ))}
        </ol>
      );
      continue;
    } else if (line.trim()) {
      elements.push(
        <p key={i} style={{ color: "#cbd5e1", fontSize: "13.5px", lineHeight: 1.75, margin: "0.4rem 0" }}
          dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#f1f5f9;font-weight:600">$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>') }}
        />
      );
    }
    i++;
  }
  return <div>{elements}</div>;
}

function SourceCard({ source, index }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(source.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div style={{ border: "1px solid rgba(148,163,184,0.12)", borderRadius: "10px", padding: "14px 16px", background: "rgba(15,23,42,0.6)", marginBottom: "10px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "20px", height: "20px", borderRadius: "4px", background: "rgba(16,185,129,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ fontSize: "10px", fontWeight: 700, color: "#10b981" }}>{index + 1}</span>
          </div>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 600, color: "#f1f5f9", letterSpacing: "0.01em" }}>
              {source.doc.replace(/_/g, " ").replace(".pdf", "")}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "4px", marginTop: "2px" }}>
              <Hash size={9} color="#64748b" />
              <span style={{ fontSize: "10px", color: "#64748b" }}>Page {source.page}</span>
            </div>
          </div>
        </div>
        <button onClick={handleCopy} style={{ background: "transparent", border: "none", cursor: "pointer", padding: "4px", color: copied ? "#10b981" : "#475569" }}>
          {copied ? <CheckCheck size={13} /> : <Copy size={13} />}
        </button>
      </div>
      <div style={{ fontSize: "11.5px", color: "#64748b", lineHeight: 1.65, borderTop: "1px solid rgba(148,163,184,0.08)", paddingTop: "8px", fontFamily: "Georgia, serif" }}>
        "{(source.text || '').substring(0, 160)}{source.text && source.text.length > 160 ? '...' : ''}"
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div style={{ padding: "0 0 1rem" }}>
      {[100, 80, 90, 60, 75].map((w, i) => (
        <div key={i} style={{ height: "13px", borderRadius: "4px", background: "rgba(148,163,184,0.08)", marginBottom: "8px", width: `${w}%`, animation: "pulse 1.5s ease-in-out infinite", animationDelay: `${i * 0.1}s` }} />
      ))}
      <style>{`@keyframes pulse { 0%,100%{opacity:0.4} 50%{opacity:0.9} }`}</style>
    </div>
  );
}

function LandingPage({ onEnter }) {
  const [activeAudience, setActiveAudience] = useState(0);
  const audiences = [
    { icon: Scale, title: "Company Secretaries", desc: "Instant answers on ROC filings, board resolutions, and statutory deadlines — with exact section references." },
    { icon: Briefcase, title: "Corporate Lawyers", desc: "Deep-dive into penalties, interpretations, and cross-reference clauses without flipping through 500-page PDFs." },
    { icon: Building2, title: "Founders & CFOs", desc: "Understand your compliance obligations before your next board meeting or funding round." },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#060d1a", color: "#f1f5f9", fontFamily: "'DM Sans', system-ui, sans-serif", overflowX: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Serif+Display:ital@0;1&display=swap');
        * { box-sizing: border-box; }
        .glow-btn:hover { background: rgba(16,185,129,0.12) !important; border-color: #10b981 !important; transform: translateY(-1px); }
        .glow-btn { transition: all 0.2s ease; }
        .aud-card:hover { border-color: rgba(16,185,129,0.3) !important; background: rgba(16,185,129,0.04) !important; }
        .aud-card { transition: all 0.2s ease; cursor: pointer; }
        @keyframes fadeUp { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:translateY(0); } }
        @keyframes shimmer { 0%{left:-100%} 100%{left:200%} }
        .hero-badge { animation: fadeUp 0.6s ease 0.1s both; }
        .hero-h1 { animation: fadeUp 0.6s ease 0.2s both; }
        .hero-sub { animation: fadeUp 0.6s ease 0.35s both; }
        .hero-btns { animation: fadeUp 0.6s ease 0.5s both; }
        .hero-card { animation: fadeUp 0.6s ease 0.65s both; }
      `}</style>

      {/* Nav */}
      <nav style={{ borderBottom: "1px solid rgba(148,163,184,0.08)", padding: "0 2rem", height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, background: "rgba(6,13,26,0.92)", backdropFilter: "blur(12px)", zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ width: "30px", height: "30px", borderRadius: "8px", background: "linear-gradient(135deg, #10b981, #0ea5e9)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Scale size={16} color="#fff" />
          </div>
          <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: "18px", letterSpacing: "-0.02em", color: "#f1f5f9" }}>CompliCS</span>
          <span style={{ fontSize: "10px", background: "rgba(16,185,129,0.15)", color: "#10b981", padding: "2px 8px", borderRadius: "20px", fontWeight: 600, letterSpacing: "0.04em", border: "1px solid rgba(16,185,129,0.25)" }}>BETA</span>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ fontSize: "12px", color: "#64748b", marginRight: "4px" }}>Companies Act 2013 · LLP Act 2008</span>
          <button onClick={onEnter} style={{ fontSize: "13px", fontWeight: 600, padding: "7px 18px", borderRadius: "8px", background: "#10b981", border: "none", color: "#fff", cursor: "pointer", letterSpacing: "0.01em" }}>
            Enter Workspace
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ maxWidth: "1100px", margin: "0 auto", padding: "80px 2rem 60px" }}>
        <div className="hero-badge" style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: "20px", padding: "5px 14px", marginBottom: "28px" }}>
          <CircleDot size={11} color="#10b981" />
          <span style={{ fontSize: "12px", color: "#10b981", fontWeight: 500, letterSpacing: "0.03em" }}>RAG-POWERED · ZERO HALLUCINATION</span>
        </div>
        <h1 className="hero-h1" style={{ fontFamily: "'DM Serif Display', serif", fontSize: "clamp(40px, 6vw, 68px)", lineHeight: 1.1, letterSpacing: "-0.03em", color: "#f8fafc", margin: "0 0 20px", maxWidth: "800px" }}>
          Navigate Indian Corporate Law with{" "}
          <em style={{ color: "#10b981", fontStyle: "italic" }}>AI-Powered Precision.</em>
        </h1>
        <p className="hero-sub" style={{ fontSize: "17px", color: "#94a3b8", lineHeight: 1.7, maxWidth: "580px", margin: "0 0 36px", fontWeight: 300 }}>
          CompliCS answers your compliance questions using only <strong style={{ color: "#e2e8f0", fontWeight: 500 }}>official statutory text</strong> — Companies Act 2013 and LLP Act 2008. Every answer is grounded in law, not guesswork.
        </p>
        <div className="hero-btns" style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <button onClick={onEnter} className="glow-btn" style={{ display: "flex", alignItems: "center", gap: "8px", padding: "13px 28px", borderRadius: "10px", background: "#10b981", border: "1px solid #10b981", color: "#fff", fontSize: "14px", fontWeight: 600, cursor: "pointer", letterSpacing: "0.01em" }}>
            Enter the Workspace <ArrowRight size={15} />
          </button>
          <button className="glow-btn" style={{ display: "flex", alignItems: "center", gap: "8px", padding: "13px 24px", borderRadius: "10px", background: "transparent", border: "1px solid rgba(148,163,184,0.2)", color: "#94a3b8", fontSize: "14px", cursor: "pointer" }}>
            <Layers size={14} /> How it Works
          </button>
        </div>

        {/* Mock Preview Card */}
        <div className="hero-card" style={{ marginTop: "60px", background: "rgba(15,23,42,0.7)", border: "1px solid rgba(148,163,184,0.12)", borderRadius: "16px", overflow: "hidden", backdropFilter: "blur(8px)" }}>
          <div style={{ padding: "12px 16px", borderBottom: "1px solid rgba(148,163,184,0.08)", display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#ef4444" }} />
            <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#f59e0b" }} />
            <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#10b981" }} />
            <span style={{ marginLeft: "8px", fontSize: "11px", color: "#475569", letterSpacing: "0.04em" }}>COMPLICS WORKSPACE</span>
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "6px" }}>
              <CircleDot size={9} color="#10b981" />
              <span style={{ fontSize: "10px", color: "#10b981", fontWeight: 500 }}>RAG ACTIVE</span>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0 }}>
            <div style={{ padding: "28px 28px", borderRight: "1px solid rgba(148,163,184,0.08)" }}>
              <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "14px", letterSpacing: "0.04em", fontWeight: 500 }}>USER QUERY</div>
              <div style={{ background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.15)", borderRadius: "10px", padding: "14px 16px", fontSize: "14px", color: "#e2e8f0", lineHeight: 1.5 }}>
                "What is the penalty for a director who fails to disclose his interest in a contract under the Companies Act 2013?"
              </div>
              <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "6px" }}>
                <Database size={12} color="#0ea5e9" />
                <span style={{ fontSize: "11px", color: "#0ea5e9" }}>Querying ChromaDB vector store...</span>
              </div>
              <div style={{ marginTop: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                <Sparkles size={12} color="#a78bfa" />
                <span style={{ fontSize: "11px", color: "#a78bfa" }}>Generating with Mistral LLM...</span>
              </div>
            </div>
            <div style={{ padding: "28px 28px" }}>
              <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "14px", letterSpacing: "0.04em", fontWeight: 500 }}>AI-VERIFIED ANSWER</div>
              <div style={{ fontSize: "13.5px", color: "#cbd5e1", lineHeight: 1.7, marginBottom: "14px" }}>
                Under <strong style={{ color: "#f1f5f9" }}>Section 184</strong>, a director who fails to disclose his interest is liable to a fine of not less than <strong style={{ color: "#10b981" }}>₹50,000</strong> extending to <strong style={{ color: "#10b981" }}>₹1 Lakh</strong>.
              </div>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: "5px", background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.25)", borderRadius: "6px", padding: "4px 10px", fontSize: "11px", color: "#10b981", fontWeight: 500 }}>
                  <Shield size={10} /> Companies Act 2013
                </span>
                <span style={{ display: "inline-flex", alignItems: "center", gap: "5px", background: "rgba(14,165,233,0.1)", border: "1px solid rgba(14,165,233,0.25)", borderRadius: "6px", padding: "4px 10px", fontSize: "11px", color: "#7dd3fc", fontWeight: 500 }}>
                  <FileText size={10} /> Pg. 178 · Sec. 184
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section style={{ background: "rgba(15,23,42,0.4)", borderTop: "1px solid rgba(148,163,184,0.06)", borderBottom: "1px solid rgba(148,163,184,0.06)", padding: "80px 2rem" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "56px" }}>
            <div style={{ fontSize: "11px", color: "#10b981", letterSpacing: "0.1em", fontWeight: 600, marginBottom: "12px" }}>THE ARCHITECTURE</div>
            <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: "clamp(28px, 4vw, 44px)", color: "#f8fafc", letterSpacing: "-0.02em", margin: 0 }}>
              How CompliCS Eliminates Hallucination
            </h2>
            <p style={{ fontSize: "15px", color: "#64748b", marginTop: "12px", maxWidth: "500px", margin: "12px auto 0" }}>
              Unlike generic AI, every answer is generated <em>strictly</em> from retrieved statutory text — never from model memory.
            </p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "2px", position: "relative" }}>
            {[
              {
                step: "01", icon: MessageSquare, color: "#0ea5e9", bg: "rgba(14,165,233,0.1)",
                title: "Ask in Plain English",
                desc: "Type your compliance question naturally. No legal codes required. 'Can a company give a loan to its director?' works perfectly.",
              },
              {
                step: "02", icon: Database, color: "#a78bfa", bg: "rgba(167,139,250,0.1)",
                title: "Semantic Vector Search",
                desc: "Your query is embedded and matched against our ChromaDB index of the MCA statutory corpus — finding the most legally relevant passages.",
              },
              {
                step: "03", icon: Sparkles, color: "#10b981", bg: "rgba(16,185,129,0.1)",
                title: "Grounded Generation",
                desc: "Mistral LLM synthesizes an answer using only the retrieved text. The raw source snippets are shown alongside every answer.",
              },
            ].map((item, i) => (
              <div key={i} style={{ background: "rgba(15,23,42,0.7)", border: "1px solid rgba(148,163,184,0.1)", borderRadius: "14px", padding: "32px 28px", position: "relative", overflow: "hidden" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
                  <div style={{ width: "44px", height: "44px", borderRadius: "12px", background: item.bg, border: `1px solid ${item.color}30`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <item.icon size={20} color={item.color} />
                  </div>
                  <span style={{ fontSize: "28px", fontFamily: "'DM Serif Display', serif", color: "rgba(148,163,184,0.12)", fontWeight: 700 }}>{item.step}</span>
                </div>
                <div style={{ fontSize: "16px", fontWeight: 600, color: "#f1f5f9", marginBottom: "10px", letterSpacing: "-0.01em" }}>{item.title}</div>
                <div style={{ fontSize: "13.5px", color: "#64748b", lineHeight: 1.7 }}>{item.desc}</div>
                {i < 2 && (
                  <div style={{ position: "absolute", right: "-12px", top: "50%", transform: "translateY(-50%)", width: "24px", height: "24px", background: "#0f172a", border: "1px solid rgba(148,163,184,0.12)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 2 }}>
                    <ArrowRight size={11} color="#475569" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Audience */}
      <section style={{ maxWidth: "1100px", margin: "0 auto", padding: "80px 2rem" }}>
        <div style={{ textAlign: "center", marginBottom: "48px" }}>
          <div style={{ fontSize: "11px", color: "#10b981", letterSpacing: "0.1em", fontWeight: 600, marginBottom: "12px" }}>WHO IT'S FOR</div>
          <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: "clamp(26px, 3vw, 38px)", color: "#f8fafc", letterSpacing: "-0.02em", margin: 0 }}>Built for India's Legal Ecosystem</h2>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
          {audiences.map((a, i) => (
            <div key={i} className="aud-card" onClick={() => setActiveAudience(i)} style={{ border: `1px solid ${activeAudience === i ? "rgba(16,185,129,0.3)" : "rgba(148,163,184,0.1)"}`, borderRadius: "14px", padding: "28px 24px", background: activeAudience === i ? "rgba(16,185,129,0.04)" : "rgba(15,23,42,0.6)" }}>
              <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: activeAudience === i ? "rgba(16,185,129,0.15)" : "rgba(148,163,184,0.06)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "16px" }}>
                <a.icon size={18} color={activeAudience === i ? "#10b981" : "#64748b"} />
              </div>
              <div style={{ fontSize: "15px", fontWeight: 600, color: "#f1f5f9", marginBottom: "8px" }}>{a.title}</div>
              <div style={{ fontSize: "13px", color: "#64748b", lineHeight: 1.65 }}>{a.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{ borderTop: "1px solid rgba(148,163,184,0.06)", padding: "80px 2rem", textAlign: "center" }}>
        <div style={{ maxWidth: "600px", margin: "0 auto" }}>
          <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: "clamp(28px, 4vw, 46px)", color: "#f8fafc", letterSpacing: "-0.02em", margin: "0 0 16px" }}>
            Your compliance workspace awaits.
          </h2>
          <p style={{ fontSize: "15px", color: "#64748b", lineHeight: 1.7, marginBottom: "32px" }}>
            Powered by verified statutory text. No hallucinations. No generic advice.
          </p>
          <button onClick={onEnter} style={{ display: "inline-flex", alignItems: "center", gap: "10px", padding: "16px 40px", borderRadius: "12px", background: "linear-gradient(135deg, #10b981, #0ea5e9)", border: "none", color: "#fff", fontSize: "16px", fontWeight: 600, cursor: "pointer", letterSpacing: "0.01em", transition: "transform 0.2s", boxShadow: "0 0 40px rgba(16,185,129,0.25)" }}>
            Enter the Workspace <ArrowRight size={18} />
          </button>
          <div style={{ marginTop: "20px", fontSize: "12px", color: "#475569" }}>
            Companies Act 2013 · LLP Act 2008 
          </div>
        </div>
      </section>
    </div>
  );
}

function Workspace({ onBack }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState([]);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
  const textarea = textareaRef.current;
  if (!textarea) return;

  // Reset to auto first so scrollHeight shrinks correctly when deleting text
  textarea.style.height = "auto";

  // Clamp between one line (~44px) and 5 lines (~180px)
  const MIN_HEIGHT = 44;
  const MAX_HEIGHT = 180;
  const newHeight = Math.min(Math.max(textarea.scrollHeight, MIN_HEIGHT), MAX_HEIGHT);

  textarea.style.height = `${newHeight}px`;

  // Only show scrollbar when content exceeds the max cap
  textarea.style.overflowY = textarea.scrollHeight > MAX_HEIGHT ? "auto" : "hidden";
}, [input]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = async (question) => {
    const q = question || input.trim();
    if (!q) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setLoading(true);
    setSources([]);
    setSourcesOpen(false);
    try {
      const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      if (!res.ok) {
        throw new Error(`Server responded with ${res.status}`);
      }
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer, sources: data.sources }]);
      setSources(data.sources || []);
      if (data.sources?.length) setSourcesOpen(true);
    } catch (err) {
      const errorMsg = `## ⚠️ Connection Error\n\nCould not reach the CompliCS backend server.\n\n**Details:** ${err.message}\n\n### How to Fix\n1. Make sure the FastAPI server is running: \`cd backend && python server.py\`\n2. Verify it is accessible at ${API_URL}/health\n3. Check if Ollama is running with the Mistral model loaded`;
      setMessages((prev) => [...prev, { role: "assistant", content: errorMsg, sources: [] }]);
    }
    setLoading(false);
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
  };

  const docs = [
    { name: "Companies Act 2013", color: "#10b981" },
    { name: "LLP Act 2008", color: "#0ea5e9" },
  ];

  return (
    <div style={{ height: "100vh", background: "#060d1a", display: "flex", flexDirection: "column", fontFamily: "'DM Sans', system-ui, sans-serif", overflow: "hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Serif+Display:ital@0;1&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 5px; } ::-webkit-scrollbar-track { background: transparent; } ::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.15); border-radius: 10px; }
        textarea:focus { outline: none; }
        .qa-btn:hover { background: rgba(16,185,129,0.08) !important; border-color: rgba(16,185,129,0.3) !important; }
        .qa-btn { transition: all 0.15s ease; cursor: pointer; }
        @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        .msg-in { animation: fadeIn 0.25s ease both; }
        @keyframes spin { to{transform:rotate(360deg)} }
      `}</style>

      {/* Top Bar */}
      <div style={{ height: "52px", borderBottom: "1px solid rgba(148,163,184,0.08)", display: "flex", alignItems: "center", paddingLeft: "16px", paddingRight: "16px", gap: "12px", flexShrink: 0, background: "rgba(6,13,26,0.95)" }}>
        <button onClick={() => setSidebarOpen(!sidebarOpen)} style={{ background: "transparent", border: "none", cursor: "pointer", color: "#475569", padding: "4px" }}>
          <Menu size={16} />
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "24px", height: "24px", borderRadius: "6px", background: "linear-gradient(135deg,#10b981,#0ea5e9)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Scale size={13} color="#fff" />
          </div>
          <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: "15px", color: "#f1f5f9" }}>CompliCS</span>
        </div>
        <div style={{ width: "1px", height: "20px", background: "rgba(148,163,184,0.12)" }} />
        <span style={{ fontSize: "12px", color: "#475569" }}>Legal Compliance Workspace</span>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "5px", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: "6px", padding: "3px 10px" }}>
            <CircleDot size={9} color="#10b981" />
            <span style={{ fontSize: "10px", color: "#10b981", fontWeight: 600, letterSpacing: "0.03em" }}>ZERO-HALLUCINATION MODE</span>
          </div>
          <button onClick={onBack} style={{ background: "transparent", border: "1px solid rgba(148,163,184,0.12)", borderRadius: "6px", padding: "4px 12px", color: "#64748b", fontSize: "12px", cursor: "pointer" }}>← Landing</button>
        </div>
      </div>

      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>

        {/* Sidebar */}
        {sidebarOpen && (
          <div style={{ width: "240px", borderRight: "1px solid rgba(148,163,184,0.08)", display: "flex", flexDirection: "column", flexShrink: 0, background: "rgba(9,16,31,0.8)", overflow: "hidden" }}>
            <div style={{ padding: "16px 14px" }}>
              <button onClick={() => { setMessages([]); setSources([]); setSourcesOpen(false); }} style={{ width: "100%", display: "flex", alignItems: "center", gap: "8px", padding: "9px 14px", borderRadius: "8px", background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.25)", color: "#10b981", fontSize: "13px", fontWeight: 600, cursor: "pointer" }}>
                <Plus size={14} /> New Compliance Query
              </button>
            </div>

            <div style={{ padding: "0 14px 10px" }}>
              <div style={{ fontSize: "10px", color: "#334155", letterSpacing: "0.08em", fontWeight: 600, marginBottom: "10px" }}>DOCUMENT VAULT</div>
              {docs.map((doc, i) => (
                <div key={i} style={{ padding: "10px 12px", borderRadius: "8px", background: "rgba(15,23,42,0.6)", border: "1px solid rgba(148,163,184,0.08)", marginBottom: "6px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                    <span style={{ fontSize: "12px", fontWeight: 500, color: "#e2e8f0" }}>{doc.name}</span>
                    <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: doc.color, flexShrink: 0 }} />
                  </div>
                  <div style={{ fontSize: "10px", color: "#475569" }}>{doc.pages} · {doc.chunks}</div>
                  <div style={{ display: "inline-flex", alignItems: "center", gap: "4px", marginTop: "5px", background: `${doc.color}15`, borderRadius: "4px", padding: "2px 6px" }}>
                    <CircleDot size={8} color={doc.color} />
                    <span style={{ fontSize: "9px", color: doc.color, fontWeight: 600, letterSpacing: "0.04em" }}>INDEXED & ACTIVE</span>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ padding: "0 14px", marginTop: "auto", paddingBottom: "16px" }}>
              <div style={{ fontSize: "10px", color: "#334155", letterSpacing: "0.08em", fontWeight: 600, marginBottom: "8px" }}>RAG PIPELINE</div>
              <div style={{ padding: "10px 12px", borderRadius: "8px", background: "rgba(15,23,42,0.4)", border: "1px solid rgba(148,163,184,0.06)", fontSize: "11px", color: "#475569", lineHeight: 1.7 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Embeddings</span><span style={{ color: "#64748b" }}>Ollama</span></div>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Vector DB</span><span style={{ color: "#64748b" }}>ChromaDB</span></div>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>LLM</span><span style={{ color: "#64748b" }}>Mistral 7B</span></div>
                <div style={{ display: "flex", justifyContent: "space-between" }}><span>Framework</span><span style={{ color: "#64748b" }}>LangChain</span></div>
              </div>
            </div>
          </div>
        )}

        {/* Chat Pane */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
          <div style={{ flex: 1, overflowY: "auto", padding: "24px 32px" }}>
            {messages.length === 0 && (
              <div style={{ maxWidth: "580px", margin: "40px auto 0" }}>
                <div style={{ textAlign: "center", marginBottom: "40px" }}>
                  <div style={{ width: "52px", height: "52px", borderRadius: "14px", background: "linear-gradient(135deg,#10b981,#0ea5e9)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
                    <Scale size={24} color="#fff" />
                  </div>
                  <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: "22px", color: "#f1f5f9", margin: "0 0 8px", letterSpacing: "-0.01em" }}>Ask a Compliance Question</h2>
                  <p style={{ fontSize: "13px", color: "#475569", lineHeight: 1.6, margin: 0 }}>
                    Every answer is grounded in retrieved statutory text from the MCA corpus. Sources are always cited.
                  </p>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  {QUICK_ACTIONS.map((qa, i) => (
                    <button key={i} className="qa-btn" onClick={() => handleSubmit(qa.query)} style={{ textAlign: "left", padding: "14px 16px", borderRadius: "10px", background: "rgba(15,23,42,0.6)", border: "1px solid rgba(148,163,184,0.1)", color: "#94a3b8", width: "100%", display: "flex", flexDirection: "column", gap: "6px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
                        <qa.icon size={13} color="#10b981" />
                        <span style={{ fontSize: "12px", fontWeight: 600, color: "#e2e8f0", letterSpacing: "0.01em" }}>{qa.label}</span>
                      </div>
                      <span style={{ fontSize: "11.5px", color: "#475569", lineHeight: 1.5 }}>{qa.query.substring(0, 65)}…</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className="msg-in" style={{ marginBottom: "20px", display: "flex", gap: "12px", flexDirection: msg.role === "user" ? "row-reverse" : "row", maxWidth: "760px", margin: "0 auto 20px" }}>
                <div style={{ width: "28px", height: "28px", borderRadius: msg.role === "user" ? "8px" : "50%", flexShrink: 0, background: msg.role === "user" ? "rgba(14,165,233,0.15)" : "linear-gradient(135deg,#10b981,#0ea5e9)", display: "flex", alignItems: "center", justifyContent: "center", border: msg.role === "user" ? "1px solid rgba(14,165,233,0.25)" : "none" }}>
                  {msg.role === "user" ? <MessageSquare size={13} color="#7dd3fc" /> : <Scale size={13} color="#fff" />}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  {msg.role === "user" ? (
                    <div style={{ background: "rgba(14,165,233,0.08)", border: "1px solid rgba(14,165,233,0.15)", borderRadius: "10px", padding: "12px 16px", fontSize: "14px", color: "#e2e8f0", lineHeight: 1.6, display: "inline-block", maxWidth: "100%" }}>
                      {msg.content}
                    </div>
                  ) : (
                    <div style={{ background: "rgba(15,23,42,0.7)", border: "1px solid rgba(148,163,184,0.1)", borderRadius: "12px", padding: "18px 20px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "12px", paddingBottom: "10px", borderBottom: "1px solid rgba(148,163,184,0.08)" }}>
                        <Shield size={11} color="#10b981" />
                        <span style={{ fontSize: "10px", color: "#10b981", fontWeight: 600, letterSpacing: "0.04em" }}>VERIFIED BY COMPLICS</span>
                        {msg.sources?.length > 0 && (
                          <span style={{ marginLeft: "auto", fontSize: "10px", color: "#475569" }}>{msg.sources.length} sources retrieved</span>
                        )}
                      </div>
                      <MarkdownRenderer content={msg.content} />
                      {msg.sources?.length > 0 && (
                        <button onClick={() => { setSources(msg.sources); setSourcesOpen(true); }} style={{ marginTop: "12px", display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "11.5px", color: "#0ea5e9", background: "rgba(14,165,233,0.06)", border: "1px solid rgba(14,165,233,0.2)", borderRadius: "6px", padding: "4px 12px", cursor: "pointer" }}>
                          <FileText size={11} /> View {msg.sources.length} Legal Sources <ChevronRight size={10} />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="msg-in" style={{ maxWidth: "760px", margin: "0 auto 20px", display: "flex", gap: "12px" }}>
                <div style={{ width: "28px", height: "28px", borderRadius: "50%", background: "linear-gradient(135deg,#10b981,#0ea5e9)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <Scale size={13} color="#fff" />
                </div>
                <div style={{ flex: 1, background: "rgba(15,23,42,0.7)", border: "1px solid rgba(148,163,184,0.1)", borderRadius: "12px", padding: "18px 20px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "12px" }}>
                    <div style={{ width: "8px", height: "8px", borderRadius: "50%", border: "1.5px solid #10b981", borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
                    <span style={{ fontSize: "11px", color: "#10b981" }}>Retrieving from ChromaDB · Generating with Mistral...</span>
                  </div>
                  <LoadingSkeleton />
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div style={{ padding: "16px 32px", borderTop: "1px solid rgba(148,163,184,0.08)", background: "rgba(6,13,26,0.9)", flexShrink: 0 }}>
            <div style={{ maxWidth: "760px", margin: "0 auto", position: "relative" }}>
              <div style={{ display: "flex", alignItems: "flex-end", gap: "10px", background: "rgba(15,23,42,0.8)", border: "1px solid rgba(148,163,184,0.15)", borderRadius: "12px", padding: "12px 14px", transition: "border-color 0.2s" }}>
                <textarea
                    ref={textareaRef}          // ← swap from inputRef to textareaRef
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKey}
                    placeholder="Ask about Companies Act, LLP Act compliance..."
                    style={{
                      flex: 1,
                      background: "transparent",
                      border: "none",
                      resize: "none",          // ← disable manual drag-resize
                      color: "#e2e8f0",
                      fontSize: "14px",
                      lineHeight: "22px",
                      fontFamily: "inherit",
                      outline: "none",
                      minHeight: "44px",       // ← replaces rows={1}
                      height: "44px",          // ← initial height, JS takes over after first render
                      overflowY: "hidden",     // ← JS will switch to "auto" when capped
                      display: "block",
                      width: "100%",
                    }}
                  />
                <button onClick={() => handleSubmit()} disabled={!input.trim() || loading} style={{ width: "34px", height: "34px", borderRadius: "8px", background: input.trim() ? "#10b981" : "rgba(148,163,184,0.08)", border: "none", display: "flex", alignItems: "center", justifyContent: "center", cursor: input.trim() ? "pointer" : "not-allowed", flexShrink: 0, transition: "background 0.2s" }}>
                  <SendHorizontal size={15} color={input.trim() ? "#fff" : "#475569"} />
                </button>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginTop: "8px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                  <Shield size={10} color="#10b981" />
                  <span style={{ fontSize: "10px", color: "#334155" }}>Answers grounded in statutory text only</span>
                </div>
                <span style={{ fontSize: "10px", color: "#1e293b" }}>·</span>
                <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                  <CornerDownLeft size={10} color="#334155" />
                  <span style={{ fontSize: "10px", color: "#334155" }}>Enter to send</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sources Pane */}
        {sourcesOpen && (
          <div style={{ width: "300px", borderLeft: "1px solid rgba(148,163,184,0.08)", display: "flex", flexDirection: "column", flexShrink: 0, background: "rgba(9,16,31,0.9)", overflow: "hidden" }}>
            <div style={{ padding: "14px 16px", borderBottom: "1px solid rgba(148,163,184,0.08)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <div style={{ fontSize: "11px", fontWeight: 600, color: "#f1f5f9", letterSpacing: "0.04em" }}>RAG TRANSPARENCY ENGINE</div>
                <div style={{ fontSize: "10px", color: "#475569", marginTop: "2px" }}>{sources.length} passages retrieved</div>
              </div>
              <button onClick={() => setSourcesOpen(false)} style={{ background: "transparent", border: "none", cursor: "pointer", color: "#475569", padding: "4px" }}>
                <X size={14} />
              </button>
            </div>
            <div style={{ flex: 1, overflowY: "auto", padding: "14px 14px" }}>
              <div style={{ background: "rgba(16,185,129,0.05)", border: "1px solid rgba(16,185,129,0.12)", borderRadius: "8px", padding: "10px 12px", marginBottom: "14px", display: "flex", gap: "8px", alignItems: "flex-start" }}>
                <Shield size={13} color="#10b981" style={{ flexShrink: 0, marginTop: "1px" }} />
                <span style={{ fontSize: "11px", color: "#64748b", lineHeight: 1.6 }}>
                  These are the raw text passages retrieved from ChromaDB before generation. The answer is synthesized exclusively from these sources.
                </span>
              </div>
              <div style={{ fontSize: "10px", color: "#334155", letterSpacing: "0.08em", fontWeight: 600, marginBottom: "10px" }}>LEGAL CITATIONS</div>
              {sources.map((src, i) => (
                <SourceCard key={i} source={src} index={i} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState("landing");
  return view === "landing"
    ? <LandingPage onEnter={() => setView("workspace")} />
    : <Workspace onBack={() => setView("landing")} />;
}
