import { Star, MessageCircle, Headphones, Users, TrendingUp, Award } from 'lucide-react';

export default function Membership() {
  return (
    <section id="membership" className="py-24 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
            The QuantTrade Advantage
          </h2>
          <p className="text-xl text-slate-400 max-w-3xl mx-auto">
            Membership extends beyond returns. Join an elite network of sophisticated investors with exclusive benefits.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-8 hover:border-cyan-500/50 transition-all duration-300 group">
            <div className="w-14 h-14 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Star className="w-7 h-7 text-cyan-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">
              Exclusive Strategy Access
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Access to proprietary algorithms unavailable on public platforms, including early entry to new strategies before capacity limits.
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-8 hover:border-fuchsia-500/50 transition-all duration-300 group">
            <div className="w-14 h-14 bg-gradient-to-br from-fuchsia-500/20 to-pink-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <MessageCircle className="w-7 h-7 text-fuchsia-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">
              Direct Team Communication
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Private Telegram channel with development team for strategy insights, performance updates, and platform development input.
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-8 hover:border-pink-500/50 transition-all duration-300 group">
            <div className="w-14 h-14 bg-gradient-to-br from-pink-500/20 to-orange-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Headphones className="w-7 h-7 text-pink-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">
              Priority Support
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Dedicated support team with 2-hour response time for urgent matters. Your questions never go unanswered.
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-8 hover:border-orange-500/50 transition-all duration-300 group">
            <div className="w-14 h-14 bg-gradient-to-br from-orange-500/20 to-emerald-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Users className="w-7 h-7 text-orange-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">
              Community Insights
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Learn from experienced members. Share market perspectives. Benefit from collective intelligence of sophisticated investors.
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-8 hover:border-emerald-500/50 transition-all duration-300 group">
            <div className="w-14 h-14 bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <TrendingUp className="w-7 h-7 text-emerald-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">
              Performance Transparency
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Real-time portfolio tracking, detailed transaction history, and comprehensive performance analytics at your fingertips.
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-xl p-8 hover:border-cyan-500/50 transition-all duration-300 group">
            <div className="w-14 h-14 bg-gradient-to-br from-cyan-500/20 to-fuchsia-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Award className="w-7 h-7 text-cyan-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">
              Referral Rewards
            </h3>
            <p className="text-slate-400 leading-relaxed">
              Earn 5% commission on referred investments. Grow your returns by expanding the community with qualified members.
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-900/80 to-slate-950/80 backdrop-blur-sm border border-slate-700 rounded-2xl p-10">
          <div className="text-center max-w-3xl mx-auto">
            <h3 className="text-2xl font-semibold text-white mb-4">
              What We Expect from Members
            </h3>
            <div className="grid sm:grid-cols-2 gap-4 text-left">
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full mt-2 flex-shrink-0"></div>
                <p className="text-slate-400">
                  <span className="text-white font-medium">Discretion:</span> Strategy details and community discussions remain confidential
                </p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 bg-fuchsia-400 rounded-full mt-2 flex-shrink-0"></div>
                <p className="text-slate-400">
                  <span className="text-white font-medium">Sophistication:</span> Understanding of market risks and investment principles
                </p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 bg-pink-400 rounded-full mt-2 flex-shrink-0"></div>
                <p className="text-slate-400">
                  <span className="text-white font-medium">Professionalism:</span> Respectful engagement with team and community members
                </p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full mt-2 flex-shrink-0"></div>
                <p className="text-slate-400">
                  <span className="text-white font-medium">Long-term Focus:</span> Emphasis on sustained performance over quick gains
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
