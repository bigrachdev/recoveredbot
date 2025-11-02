import { ArrowRight, TrendingUp, Lock, Users } from 'lucide-react';

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden px-4 sm:px-6 lg:px-8 pt-20">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxNCAwIDYtMi42ODYgNi02cy0yLjY4Ni02LTYtNi02IDIuNjg2LTYgNiAyLjY4NiA2IDYgNiIgc3Ryb2tlPSJyZ2JhKDEwMCwgMjAwLCAyNTUsIDAuMSkiLz48L2c+PC9zdmc+')] opacity-30"></div>

      <div className="relative z-10 max-w-7xl mx-auto text-center">
        <div className="flex justify-center mb-8 animate-fade-in">
          <img
            src="/4911568327780535832.png"
            alt="QuantTrade AI Logo"
            className="w-32 h-32 sm:w-40 sm:h-40 object-contain drop-shadow-2xl"
          />
        </div>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-6 tracking-tight animate-slide-up">
          Quantum Intelligence for
          <span className="block bg-gradient-to-r from-cyan-400 via-fuchsia-400 to-pink-400 bg-clip-text text-transparent mt-2">
            Algorithmic Trading
          </span>
        </h1>

        <p className="text-xl sm:text-2xl text-slate-300 mb-12 max-w-3xl mx-auto leading-relaxed animate-slide-up-delay">
          Join the exclusive community where AI-driven quantitative strategies deliver exceptional returns
        </p>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto mb-12 animate-fade-in-delay">
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6 hover:border-cyan-500/50 transition-all duration-300 hover:scale-105">
            <TrendingUp className="w-8 h-8 text-cyan-400 mx-auto mb-3" />
            <div className="text-3xl font-bold text-white mb-1">1.38% - 3.14%</div>
            <div className="text-sm text-slate-400">Daily Returns</div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6 hover:border-fuchsia-500/50 transition-all duration-300 hover:scale-105">
            <div className="w-8 h-8 bg-fuchsia-500 rounded-full mx-auto mb-3 flex items-center justify-center">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">24/7</div>
            <div className="text-sm text-slate-400">AI Trading</div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6 hover:border-pink-500/50 transition-all duration-300 hover:scale-105">
            <Users className="w-8 h-8 text-pink-400 mx-auto mb-3" />
            <div className="text-3xl font-bold text-white mb-1">2,500</div>
            <div className="text-sm text-slate-400">Elite Members</div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6 hover:border-emerald-500/50 transition-all duration-300 hover:scale-105">
            <Lock className="w-8 h-8 text-emerald-400 mx-auto mb-3" />
            <div className="text-3xl font-bold text-white mb-1">Bank-Grade</div>
            <div className="text-sm text-slate-400">Security</div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center animate-fade-in-delay-2">
          <a
            href="https://t.me/your_quanttrade_bot"
            target="_blank"
            rel="noopener noreferrer"
            className="group bg-gradient-to-r from-cyan-500 to-fuchsia-500 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:from-cyan-400 hover:to-pink-400 transition-all duration-300 shadow-lg hover:shadow-cyan-500/50 hover:scale-105 flex items-center gap-2"
          >
            Request Access
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </a>

          <a
            href="#membership"
            className="group bg-slate-800/50 backdrop-blur-sm border border-slate-700 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:border-slate-600 transition-all duration-300 hover:scale-105"
          >
            Learn More
          </a>
        </div>

        <div className="mt-16 text-sm text-slate-500 animate-fade-in-delay-3">
          Limited to 100 new members per month
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-950 to-transparent"></div>
    </section>
  );
}
