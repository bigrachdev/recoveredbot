import { ArrowRight, Send } from 'lucide-react';

export default function CTA() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-4xl mx-auto">
        <div className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-3xl overflow-hidden border border-slate-700">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxNCAwIDYtMi42ODYgNi02cy0yLjY4Ni02LTYtNi02IDIuNjg2LTYgNiAyLjY4NiA2IDYgNiIgc3Ryb2tlPSJyZ2JhKDEwMCwgMjAwLCAyNTUsIDAuMDUpIi8+PC9nPjwvc3ZnPg==')] opacity-20"></div>

          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-cyan-500/20 to-fuchsia-500/20 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-tr from-pink-500/20 to-purple-500/20 rounded-full blur-3xl"></div>

          <div className="relative z-10 p-12 text-center">
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
              Ready to Join the Elite?
            </h2>
            <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
              Limited spots available. Applications are reviewed individually to maintain community standards and strategy effectiveness.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
              <a
                href="https://t.me/your_quanttrade_bot"
                target="_blank"
                rel="noopener noreferrer"
                className="group bg-gradient-to-r from-cyan-500 to-fuchsia-500 text-white px-10 py-5 rounded-xl font-semibold text-lg hover:from-cyan-400 hover:to-pink-400 transition-all duration-300 shadow-lg hover:shadow-cyan-500/50 hover:scale-105 flex items-center gap-3 w-full sm:w-auto justify-center"
              >
                <Send className="w-5 h-5" />
                Apply for Membership
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </a>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-6 text-sm text-slate-400">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                <span>23 spots remaining this month</span>
              </div>
              <div className="hidden sm:block w-px h-4 bg-slate-700"></div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-cyan-400 rounded-full"></div>
                <span>Applications reviewed within 24h</span>
              </div>
            </div>

            <div className="mt-12 pt-8 border-t border-slate-700/50">
              <p className="text-slate-500 text-sm mb-4">
                Not ready to commit? Join our Telegram community to learn more.
              </p>
              <a
                href="https://t.me/your_quanttrade_community"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                <Send className="w-4 h-4" />
                <span className="text-sm font-medium">Join Community Channel</span>
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-xs text-slate-600">
            Trading involves risk. Past performance does not guarantee future results. QuantTrade AI is selective and reserves the right to decline applications.
          </p>
        </div>
      </div>
    </section>
  );
}
