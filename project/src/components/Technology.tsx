import { Brain, Activity, Globe, BarChart3, Zap } from 'lucide-react';

export default function Technology() {
  const strategies = [
    {
      name: 'Trend Following',
      subtitle: 'Stable Growth',
      range: '$500 - $5,000',
      returns: '1.38%',
      icon: <BarChart3 className="w-6 h-6" />,
      color: 'from-cyan-500/20 to-blue-500/20',
      border: 'border-cyan-500/30'
    },
    {
      name: 'Momentum Trading',
      subtitle: 'High Velocity',
      range: '$6K - $15K',
      returns: '1.85%',
      icon: <Zap className="w-6 h-6" />,
      color: 'from-blue-500/20 to-fuchsia-500/20',
      border: 'border-blue-500/30'
    },
    {
      name: 'Mean Reversion',
      subtitle: 'Balanced Recovery',
      range: '$16K - $30K',
      returns: '2.26%',
      icon: <Activity className="w-6 h-6" />,
      color: 'from-fuchsia-500/20 to-pink-500/20',
      border: 'border-fuchsia-500/30'
    },
    {
      name: 'Scalping',
      subtitle: 'Quick Hits',
      range: '$31K - $50K',
      returns: '2.83%',
      icon: <Zap className="w-6 h-6" />,
      color: 'from-pink-500/20 to-orange-500/20',
      border: 'border-pink-500/30'
    },
    {
      name: 'Arbitrage',
      subtitle: 'Risk-Arbitrage',
      range: '$51K+',
      returns: '3.14%',
      icon: <Globe className="w-6 h-6" />,
      color: 'from-orange-500/20 to-emerald-500/20',
      border: 'border-emerald-500/30'
    }
  ];

  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
            Institutional-Grade AI,{' '}
            <span className="bg-gradient-to-r from-cyan-400 to-fuchsia-400 bg-clip-text text-transparent">
              Retail Accessibility
            </span>
          </h2>
          <p className="text-xl text-slate-400 max-w-3xl mx-auto">
            Proprietary quantitative algorithms refined through years of research, now available to select investors.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6 hover:border-cyan-500/50 transition-all duration-300">
            <Brain className="w-10 h-10 text-cyan-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">Machine Learning</h3>
            <p className="text-slate-400 text-sm">
              Self-improving algorithms that adapt to evolving market conditions in real-time.
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6 hover:border-fuchsia-500/50 transition-all duration-300">
            <Activity className="w-10 h-10 text-fuchsia-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">Real-Time Analysis</h3>
            <p className="text-slate-400 text-sm">
              Millisecond-level market monitoring across multiple exchanges simultaneously.
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6 hover:border-pink-500/50 transition-all duration-300">
            <Globe className="w-10 h-10 text-pink-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">Multi-Exchange</h3>
            <p className="text-slate-400 text-sm">
              Direct API connections to premium exchanges for optimal execution.
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-6 hover:border-emerald-500/50 transition-all duration-300">
            <BarChart3 className="w-10 h-10 text-emerald-400 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">Risk Management</h3>
            <p className="text-slate-400 text-sm">
              Sophisticated hedging and position sizing to protect capital.
            </p>
          </div>
        </div>

        <div className="mb-12">
          <h3 className="text-2xl font-semibold text-white text-center mb-8">
            Five Strategy Tiers
          </h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {strategies.map((strategy, index) => (
              <div
                key={index}
                className={`bg-gradient-to-br ${strategy.color} backdrop-blur-sm border ${strategy.border} rounded-xl p-6 hover:scale-105 transition-all duration-300`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="text-white">{strategy.icon}</div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white">{strategy.returns}</div>
                    <div className="text-xs text-slate-400">Daily</div>
                  </div>
                </div>
                <h4 className="text-lg font-semibold text-white mb-1">
                  {strategy.name}
                </h4>
                <p className="text-sm text-slate-300 mb-3">{strategy.subtitle}</p>
                <div className="text-xs text-slate-400 border-t border-slate-700/50 pt-3">
                  Investment Range: {strategy.range}
                </div>
              </div>
            ))}
            <div className="bg-slate-900/30 backdrop-blur-sm border border-slate-800 border-dashed rounded-xl p-6 flex items-center justify-center">
              <div className="text-center">
                <div className="text-slate-600 text-4xl mb-2">+</div>
                <p className="text-sm text-slate-500">More strategies<br />in development</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/30 backdrop-blur-sm border border-slate-800 rounded-xl p-8 text-center">
          <p className="text-slate-400 text-sm">
            Strategy selection is automatic based on your investment amount, ensuring optimal risk-adjusted returns for your portfolio size.
          </p>
        </div>
      </div>
    </section>
  );
}
