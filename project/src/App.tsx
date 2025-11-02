import Hero from './components/Hero';
import Exclusivity from './components/Exclusivity';
import Technology from './components/Technology';
import Security from './components/Security';
import Membership from './components/Membership';
import CTA from './components/CTA';
import Footer from './components/Footer';
import FloatingStats from './components/FloatingStats';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <FloatingStats />
      <Hero />
      <Exclusivity />
      <Technology />
      <Security />
      <Membership />
      <CTA />
      <Footer />
    </div>
  );
}

export default App;
