import { Shield, Target, TrendingUp, Award } from 'lucide-react';

export default function Exclusivity() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
            Why We Remain Selective
          </h2>
          <p className="text-xl text-slate-400 max-w-3xl mx-auto">
            Excellence requires exclusivity. Our limited membership model ensures sustained performance and community quality.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-16">
          <div className="group bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-8 hover:border-cyan-500/50 transition-all duration-300 hover:scale-105">
            <Shield className="w-12 h-12 text-cyan-400 mb-4" />
            <h3 className="text-2xl font-semibold text-white mb-3">
              Preserved Strategy Performance
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Limited capital allocation ensures our proprietary algorithms maintain optimal efficiency and consistent returns without market saturation.
            </p>
          </div>

          <div className="group bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-8 hover:border-fuchsia-500/50 transition-all duration-300 hover:scale-105">
            <Target className="w-12 h-12 text-fuchsia-400 mb-4" />
            <h3 className="text-2xl font-semibold text-white mb-3">
              Elite Community Quality
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Carefully vetted members create a sophisticated environment where knowledge sharing and collective intelligence amplify individual success.
            </p>
          </div>

          <div className="group bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-8 hover:border-pink-500/50 transition-all duration-300 hover:scale-105">
            <TrendingUp className="w-12 h-12 text-pink-400 mb-4" />
            <h3 className="text-2xl font-semibold text-white mb-3">
              Optimal Capital Allocation
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Strategic fund distribution across our algorithm suite ensures maximum execution quality and minimal slippage on every trade.
            </p>
          </div>

          <div className="group bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-8 hover:border-emerald-500/50 transition-all duration-300 hover:scale-105">
            <Award className="w-12 h-12 text-emerald-400 mb-4" />
            <h3 className="text-2xl font-semibold text-white mb-3">
              Sustained Competitive Edge
            </h3>
            <p className="text-slate-400 leading-relaxed">
              By remaining under the radar, we avoid the performance degradation that inevitably follows mass market exposure.
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-r from-slate-800/50 to-slate-900/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-12 text-center">
          <div className="flex flex-col md:flex-row justify-center items-center gap-8 md:gap-16">
            <div>
              <div className="text-5xl font-bold bg-gradient-to-r from-cyan-400 to-fuchsia-400 bg-clip-text text-transparent mb-2">
                2,500
              </div>
              <div className="text-slate-400 text-sm uppercase tracking-wider">Vetted Members</div>
            </div>

            <div className="hidden md:block w-px h-16 bg-slate-700"></div>

            <div>
              <div className="text-5xl font-bold bg-gradient-to-r from-fuchsia-400 to-pink-400 bg-clip-text text-transparent mb-2">
                94%
              </div>
              <div className="text-slate-400 text-sm uppercase tracking-wider">Retention Rate</div>
            </div>

            <div className="hidden md:block w-px h-16 bg-slate-700"></div>

            <div>
              <div className="text-5xl font-bold bg-gradient-to-r from-pink-400 to-emerald-400 bg-clip-text text-transparent mb-2">
                100
              </div>
              <div className="text-slate-400 text-sm uppercase tracking-wider">Monthly Openings</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
