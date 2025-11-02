import { useEffect, useState } from 'react';

interface CryptoPrice {
  symbol: string;
  price: number;
  change: number;
}

export default function FloatingStats() {
  const [cryptoPrices, setCryptoPrices] = useState<CryptoPrice[]>([
    { symbol: 'BTC', price: 67234.56, change: 2.34 },
    { symbol: 'ETH', price: 3456.78, change: -1.23 },
    { symbol: 'SOL', price: 145.32, change: 5.67 },
    { symbol: 'BNB', price: 412.89, change: 1.45 },
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCryptoPrices((prev) =>
        prev.map((crypto) => ({
          ...crypto,
          price: crypto.price * (1 + (Math.random() - 0.5) * 0.002),
          change: crypto.change + (Math.random() - 0.5) * 0.5,
        }))
      );
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/50">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4 overflow-x-auto">
          <div className="flex items-center gap-2 flex-shrink-0">
            <img src="/4911568327780535832.png" alt="QuantTrade AI" className="w-6 h-6 object-contain" />
            <span className="text-white font-semibold text-sm hidden sm:inline">QuantTrade AI</span>
          </div>

          <div className="flex items-center gap-6 overflow-x-auto scrollbar-hide">
            {cryptoPrices.map((crypto) => (
              <div key={crypto.symbol} className="flex items-center gap-2 flex-shrink-0">
                <span className="text-slate-400 text-xs font-medium">
                  {crypto.symbol}
                </span>
                <span className="text-white text-sm font-semibold">
                  ${crypto.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span
                  className={`text-xs font-medium ${
                    crypto.change >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}
                >
                  {crypto.change >= 0 ? '+' : ''}
                  {crypto.change.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>

          <a
            href="https://t.me/your_quanttrade_bot"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden md:block bg-gradient-to-r from-cyan-500 to-fuchsia-500 text-white px-4 py-1.5 rounded-lg text-sm font-semibold hover:from-cyan-400 hover:to-pink-400 transition-all duration-300 flex-shrink-0"
          >
            Join Now
          </a>
        </div>
      </div>
    </div>
  );
}
