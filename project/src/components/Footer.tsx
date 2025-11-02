import { Send } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="relative py-16 px-4 sm:px-6 lg:px-8 border-t border-slate-800">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-3 gap-12 mb-12">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <img
                src="/4911568327780535832.png"
                alt="QuantTrade AI Logo"
                className="w-10 h-10 object-contain"
              />
              <span className="text-xl font-bold text-white">QuantTrade AI</span>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed mb-4">
              Quantum intelligence for algorithmic trading. AI-driven quantitative strategies delivering exceptional returns to sophisticated investors.
            </p>
            <div className="text-xs text-slate-600">
              Est. 2021
            </div>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Platform</h3>
            <ul className="space-y-3">
              <li>
                <a href="#membership" className="text-slate-400 hover:text-cyan-400 transition-colors text-sm">
                  Membership Benefits
                </a>
              </li>
              <li>
                <a href="https://t.me/your_quanttrade_bot" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-cyan-400 transition-colors text-sm">
                  Apply Now
                </a>
              </li>
              <li>
                <a href="/about" className="text-slate-400 hover:text-cyan-400 transition-colors text-sm">
                  About Us
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-cyan-400 transition-colors text-sm">
                  FAQ
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">Legal</h3>
            <ul className="space-y-3 mb-6">
              <li>
                <a href="/privacy" className="text-slate-400 hover:text-cyan-400 transition-colors text-sm">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="/terms" className="text-slate-400 hover:text-cyan-400 transition-colors text-sm">
                  Terms of Service
                </a>
              </li>
              <li>
                <a href="/risk" className="text-slate-400 hover:text-cyan-400 transition-colors text-sm">
                  Risk Disclosure
                </a>
              </li>
            </ul>

            <h3 className="text-white font-semibold mb-4">Community</h3>
            <a
              href="https://t.me/your_quanttrade_community"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-slate-400 hover:text-cyan-400 transition-colors text-sm group"
            >
              <Send className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              Telegram
            </a>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-800">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-slate-500 text-sm">
              {currentYear} QuantTrade AI. All rights reserved.
            </p>
            <p className="text-slate-600 text-xs text-center sm:text-right">
              Quantum Intelligence. Algorithmic Precision.
            </p>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-800/50">
          <p className="text-xs text-slate-600 text-center max-w-4xl mx-auto leading-relaxed">
            Disclaimer: Trading cryptocurrencies carries substantial risk of loss. Past performance is not indicative of future results.
            QuantTrade AI provides algorithmic trading services but does not guarantee profits. Members should only invest capital they can afford to lose.
            QuantTrade AI is not a registered investment advisor and does not provide financial advice. All investment decisions are made at the member's discretion.
          </p>
        </div>
      </div>
    </footer>
  );
}
