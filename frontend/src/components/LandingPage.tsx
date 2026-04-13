import { ArrowRight, BarChart3, BrainCircuit, ShieldCheck, Zap } from "lucide-react";

interface LandingPageProps {
  onGetStarted: () => void;
}

export function LandingPage({ onGetStarted }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-[#fafcff] font-sans text-gray-900 selection:bg-emerald-100 selection:text-emerald-900 overflow-hidden">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/70 backdrop-blur-xl border-b border-gray-100 transition-all">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-yellow-300 to-yellow-500 border-[2px] border-yellow-600 flex items-center justify-center shadow-[inset_0_-2px_4px_rgba(0,0,0,0.2),_0_2px_4px_rgba(0,0,0,0.1)] relative">
              <div className="w-6 h-6 rounded-full border border-yellow-600/40 flex items-center justify-center">
                 <span className="text-yellow-800 font-bold text-sm">¢</span>
              </div>
            </div>
            <span className="font-bold text-xl tracking-tight text-gray-900">Penny</span>
          </div>
          <button
            onClick={onGetStarted}
            className="px-5 py-2 bg-gray-900 text-white text-sm font-semibold rounded-full hover:bg-gray-800 transition-all shadow-sm hover:shadow active:scale-95"
          >
            Go to App
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-12 px-6 flex flex-col items-center justify-center">
        {/* Abstract Background Glows */}
        <div className="absolute top-[10%] left-[20%] w-[500px] h-[500px] bg-emerald-200/50 blur-[120px] rounded-full pointer-events-none mix-blend-multiply" />
        <div className="absolute bottom-[20%] right-[10%] w-[400px] h-[400px] bg-sky-200/50 blur-[120px] rounded-full pointer-events-none mix-blend-multiply" />

        <div className="relative z-10 max-w-4xl mx-auto text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white border border-emerald-100 text-emerald-700 text-sm font-semibold mb-8 shadow-sm">
            <Zap className="w-4 h-4 fill-emerald-500" />
            <span>Powered by Google Gemini API</span>
          </div>
          
          <h1 className="text-6xl md:text-8xl font-black text-gray-900 tracking-tighter mb-8 leading-[1.05]">
            Personal Finance,<br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-600">
              Supercharged by AI.
            </span>
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-500 max-w-3xl mx-auto mb-10 leading-relaxed font-medium">
            Upload your bank statements and let AI categorize your spending, discover insights, and provide actionable savings recommendations.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={onGetStarted}
              className="group px-8 py-4 bg-gray-900 text-white font-bold text-lg rounded-full hover:bg-gray-800 transition-all duration-300 flex items-center justify-center gap-2 shadow-xl shadow-gray-900/20 active:scale-95"
            >
              Start Analyzing Now
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <a 
              href="#how-it-works"
              className="px-8 py-4 bg-white text-gray-700 font-bold text-lg rounded-full hover:bg-gray-50 border border-gray-200 transition-all duration-300 flex items-center justify-center active:scale-95 shadow-sm hover:shadow"
            >
              See How It Works
            </a>
          </div>
        </div>

        {/* Hero Abstract Dashboard Mockup */}
        <div className="relative w-full max-w-4xl mx-auto perspective-1000 z-10">
          <div className="absolute inset-0 bg-gradient-to-tr from-emerald-400/20 to-sky-400/20 rounded-[2.5rem] blur-2xl transform translate-y-4"></div>
          <div className="relative bg-white/80 backdrop-blur-2xl rounded-3xl p-6 md:p-10 shadow-2xl border border-white flex flex-col gap-8">
            <div className="flex items-center justify-between border-b border-gray-100 pb-6">
              <div>
                <div className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">Current Balance</div>
                <div className="text-4xl font-extrabold text-gray-900">$8,420.50</div>
              </div>
              <div className="flex items-center gap-2 bg-emerald-50 px-4 py-2 rounded-xl border border-emerald-100">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                <span className="text-sm font-bold text-emerald-700">Live AI Analysis</span>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-50 rounded-2xl p-5 border border-gray-100">
                <div className="text-gray-500 text-sm font-medium mb-2">Dining Out</div>
                <div className="text-2xl font-bold text-gray-900 mb-2">$485.00</div>
                <div className="w-full bg-gray-200 rounded-full h-1.5"><div className="bg-orange-400 h-1.5 rounded-full w-[65%]"></div></div>
              </div>
              <div className="bg-gray-50 rounded-2xl p-5 border border-gray-100">
                <div className="text-gray-500 text-sm font-medium mb-2">Groceries</div>
                <div className="text-2xl font-bold text-gray-900 mb-2">$320.00</div>
                <div className="w-full bg-gray-200 rounded-full h-1.5"><div className="bg-emerald-400 h-1.5 rounded-full w-[45%]"></div></div>
              </div>
              <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl p-5 text-white shadow-lg transform -translate-y-2">
                <div className="text-emerald-100 text-sm font-medium mb-2 flex items-center gap-1">
                  <Zap className="w-4 h-4" /> Insight
                </div>
                <div className="text-md font-bold leading-snug">
                  "Cut dining expenses by 10% to save $48 this month."
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Showcase */}
      <section id="how-it-works" className="py-32 bg-white relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-24">
            <h2 className="text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight mb-6">Smarter Tracking, Zero Effort</h2>
            <p className="text-xl text-gray-500 text-balance max-w-2xl mx-auto">A completely automated workflow that respects your privacy. No bank logins required.</p>
          </div>

          <div className="space-y-32">
            
            {/* Feature 1: Intelligent Categorization (CSS Mockup) */}
            <div className="flex flex-col lg:flex-row items-center gap-16 lg:gap-24">
              <div className="flex-1 space-y-8">
                <div className="w-14 h-14 bg-blue-50 border border-blue-100 text-blue-600 rounded-2xl flex items-center justify-center">
                  <BrainCircuit className="w-7 h-7" />
                </div>
                <h3 className="text-3xl md:text-4xl font-bold text-gray-900 tracking-tight">Intelligent Categorization</h3>
                <p className="text-lg text-gray-600 leading-relaxed">
                  Say goodbye to manual data entry. Penny's hybrid classification engine uses lightning-fast keyword matching combined with the analytical power of the <strong>Gemini API</strong> to automatically label even the most ambiguous transactions.
                </p>
                <ul className="space-y-4 pt-2 font-medium">
                  {[
                    "Supports multiple bank CSV and PDF statements",
                    "60-70% instant matching with local rules",
                    "LLM fallback for perfect accuracy and unidentifiable vendors",
                  ].map((item, i) => (
                    <li key={i} className="flex items-start gap-4 text-gray-700">
                      <div className="mt-1 bg-emerald-50 rounded-full p-1 border border-emerald-100">
                        <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      </div>
                      <span className="leading-tight">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="flex-1 w-full perspective-1000">
                 <div className="bg-gray-50 rounded-3xl p-6 shadow-2xl border border-gray-200 transform rotate-y-[-5deg] rotate-x-[5deg]">
                    <div className="text-sm font-bold text-gray-500 mb-4 px-2 tracking-wider">RECENT TRANSACTIONS</div>
                    <div className="space-y-3">
                      {[
                        { name: "SQ *BURRITO KING 94105", cat: "Dining Out", amount: "-$12.50", icon: "🍔", color: "bg-orange-100 text-orange-600", border: "border-orange-200" },
                        { name: "UBER *TRIP SFO", cat: "Transportation", amount: "-$34.00", icon: "🚗", color: "bg-blue-100 text-blue-600", border: "border-blue-200" },
                        { name: "WHOLEFDS SOMA", cat: "Groceries", amount: "-$112.20", icon: "🛒", color: "bg-emerald-100 text-emerald-600", border: "border-emerald-200" },
                        { name: "AMZN MKTP US*8", cat: "Shopping", amount: "-$45.99", icon: "🛍️", color: "bg-purple-100 text-purple-600", border: "border-purple-200" }
                      ].map((tx, idx) => (
                        <div key={idx} className="flex items-center justify-between p-4 rounded-2xl bg-white shadow-sm border border-gray-100 hover:border-gray-200 transition-colors">
                          <div className="flex items-center gap-4">
                             <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl border ${tx.border} ${tx.color}`}>{tx.icon}</div>
                             <div>
                               <div className="font-bold text-gray-900">{tx.name}</div>
                               <div className="text-xs font-semibold text-gray-500">{tx.cat}</div>
                             </div>
                          </div>
                          <div className="font-bold text-gray-900">{tx.amount}</div>
                        </div>
                      ))}
                    </div>
                 </div>
              </div>
            </div>

            {/* Feature 2: Actionable Insights (CSS Mockup) */}
            <div className="flex flex-col lg:flex-row-reverse items-center gap-16 lg:gap-24">
              <div className="flex-1 space-y-8">
                <div className="w-14 h-14 bg-rose-50 border border-rose-100 text-rose-600 rounded-2xl flex items-center justify-center">
                  <BarChart3 className="w-7 h-7" />
                </div>
                <h3 className="text-3xl md:text-4xl font-bold text-gray-900 tracking-tight">Actionable AI Insights</h3>
                <p className="text-lg text-gray-600 leading-relaxed">
                  Charts are great, but context is better. Penny doesn't just show you pie charts; it analyzes your spending patterns month-over-month to generate personalized, specific, and achievable savings recommendations.
                </p>
                <ul className="space-y-4 pt-2 font-medium">
                  {[
                    "Discover hidden subscriptions automatically",
                    "Compare spending across different categories",
                    "Get tailored 'how-to-save' tips driven by your data",
                  ].map((item, i) => (
                    <li key={i} className="flex items-start gap-4 text-gray-700">
                      <div className="mt-1 bg-emerald-50 rounded-full p-1 border border-emerald-100">
                        <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      </div>
                      <span className="leading-tight">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="flex-1 w-full">
                 <div className="grid grid-cols-1 gap-6 relative">
                    <div className="absolute -inset-4 bg-gradient-to-r from-teal-50 to-emerald-50 rounded-[3rem] -z-10"></div>
                    
                    <div className="bg-white rounded-3xl p-6 shadow-xl border border-emerald-100 relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
                      <h4 className="font-bold text-gray-900 text-lg mb-2 flex items-center gap-2">
                        <Zap className="w-5 h-5 text-emerald-500" /> Reduce dining spending
                      </h4>
                      <p className="text-gray-600 leading-relaxed mb-4 text-sm">
                        Your dining spending of <span className="font-bold text-gray-900">$485</span> accounts for 35% of total expenses and is 40% above your 3-month average. 
                      </p>
                      <div className="bg-emerald-50 text-emerald-700 px-4 py-3 rounded-xl font-medium text-sm inline-block">
                        💡 Potential Savings: $120.00 / month
                      </div>
                    </div>

                    <div className="bg-white rounded-3xl p-6 shadow-xl border border-sky-100 relative overflow-hidden transform translate-x-4">
                      <div className="absolute top-0 left-0 w-1 h-full bg-sky-500"></div>
                      <h4 className="font-bold text-gray-900 text-lg mb-2 flex items-center gap-2">
                        <span className="text-xl">🚕</span> Reign in transportation
                      </h4>
                      <p className="text-gray-600 leading-relaxed mb-4 text-sm">
                        You took 14 Uber rides this month totaling <span className="font-bold text-gray-900">$190</span>. Consider public transit for regular commutes.
                      </p>
                      <div className="bg-sky-50 text-sky-700 px-4 py-3 rounded-xl font-medium text-sm inline-block">
                        💡 Potential Savings: $80.00 / month
                      </div>
                    </div>
                 </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 bg-gray-900 relative overflow-hidden">
        {/* Dynamic Abstract Background */}
        <div className="absolute top-0 left-1/4 w-[1000px] h-[1000px] bg-emerald-500/20 blur-[150px] rounded-full pointer-events-none mix-blend-screen opacity-40"></div>
        <div className="absolute bottom-0 right-1/4 w-[800px] h-[800px] bg-teal-500/20 blur-[150px] rounded-full pointer-events-none mix-blend-screen opacity-40"></div>

        <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
          <h2 className="text-4xl md:text-6xl font-black text-white mb-8 tracking-tight">
            Ready to Take Control?
          </h2>
          <p className="text-xl md:text-2xl text-gray-300 mb-12 max-w-2xl mx-auto font-medium leading-relaxed">
            No sign up required. Your data is processed securely in your browser session and never permanently stored. Instant, secure, and smart.
          </p>
          <button 
            onClick={onGetStarted}
            className="px-12 py-5 bg-white text-gray-900 font-bold text-xl rounded-full hover:bg-gray-100 hover:scale-105 transition-all duration-300 shadow-2xl shadow-white/10 active:scale-95"
          >
            Upload Your Statement
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-black border-t border-gray-800 text-center relative z-20">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
           <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-yellow-300 to-yellow-500 border-[1px] border-yellow-600 flex items-center justify-center shadow-inner relative">
              <div className="w-4 h-4 rounded-full border border-yellow-600/40 flex items-center justify-center">
                 <span className="text-yellow-800 font-bold text-[10px] leading-none">¢</span>
              </div>
            </div>
            <span className="font-bold text-gray-400">Penny</span>
          </div>
          <p className="text-sm text-gray-500 font-medium">
            © 2026 Penny. Built as an open-source project. Not a real financial advisor.
          </p>
        </div>
      </footer>
    </div>
  );
}
