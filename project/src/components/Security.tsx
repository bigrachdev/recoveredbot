import { Shield, Lock, Eye, FileCheck } from 'lucide-react';

export default function Security() {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 relative bg-slate-950/50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
            Bank-Level Security,{' '}
            <span className="bg-gradient-to-r from-cyan-400 to-pink-400 bg-clip-text text-transparent">
              Absolute Privacy
            </span>
          </h2>
          <p className="text-xl text-slate-400 max-w-3xl mx-auto">
            Your capital protection is our highest priority. Enterprise-grade security infrastructure safeguards every transaction.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-12">
          <div className="group relative bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-8 hover:border-cyan-500/50 transition-all duration-300 overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 rounded-full blur-3xl group-hover:bg-cyan-500/20 transition-all duration-300"></div>
            <Shield className="w-12 h-12 text-cyan-400 mb-4 relative z-10" />
            <h3 className="text-2xl font-semibold text-white mb-3 relative z-10">
              Cold Storage Protection
            </h3>
            <p className="text-slate-400 leading-relaxed relative z-10">
              95% of assets maintained in air-gapped cold storage with multi-signature authentication, ensuring maximum protection against digital threats.
            </p>
          </div>

          <div className="group relative bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-8 hover:border-fuchsia-500/50 transition-all duration-300 overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-fuchsia-500/10 rounded-full blur-3xl group-hover:bg-fuchsia-500/20 transition-all duration-300"></div>
            <Lock className="w-12 h-12 text-fuchsia-400 mb-4 relative z-10" />
            <h3 className="text-2xl font-semibold text-white mb-3 relative z-10">
              End-to-End Encryption
            </h3>
            <p className="text-slate-400 leading-relaxed relative z-10">
              AES-256 encryption for all data transmission and storage. Your sensitive information never exists in plain text on our systems.
            </p>
          </div>

          <div className="group relative bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-8 hover:border-pink-500/50 transition-all duration-300 overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-pink-500/10 rounded-full blur-3xl group-hover:bg-pink-500/20 transition-all duration-300"></div>
            <FileCheck className="w-12 h-12 text-pink-400 mb-4 relative z-10" />
            <h3 className="text-2xl font-semibold text-white mb-3 relative z-10">
              Regular Security Audits
            </h3>
            <p className="text-slate-400 leading-relaxed relative z-10">
              Quarterly penetration testing by independent security firms. Continuous monitoring for vulnerabilities and immediate remediation.
            </p>
          </div>

          <div className="group relative bg-slate-900/50 backdrop-blur-sm border border-slate-800 rounded-2xl p-8 hover:border-emerald-500/50 transition-all duration-300 overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl group-hover:bg-emerald-500/20 transition-all duration-300"></div>
            <Eye className="w-12 h-12 text-emerald-400 mb-4 relative z-10" />
            <h3 className="text-2xl font-semibold text-white mb-3 relative z-10">
              Privacy-First Approach
            </h3>
            <p className="text-slate-400 leading-relaxed relative z-10">
              Minimal data collection policy. We never share, sell, or expose your personal information. Your identity remains confidential.
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-900/80 to-slate-950/80 backdrop-blur-sm border border-slate-700 rounded-2xl p-10">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <div className="flex-shrink-0">
              <div className="w-20 h-20 bg-gradient-to-br from-cyan-500 to-fuchsia-500 rounded-2xl flex items-center justify-center">
                <Shield className="w-10 h-10 text-white" />
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-2xl font-semibold text-white mb-3">
                Your Security Responsibilities
              </h3>
              <p className="text-slate-400 leading-relaxed">
                Enable two-factor authentication on your Telegram account. Use secure networks when accessing the platform. Never share your private keys or sensitive information with anyone, including our team.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
