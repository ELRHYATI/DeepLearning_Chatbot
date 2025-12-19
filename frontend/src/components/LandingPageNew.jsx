import Navbar from './landing/Navbar'
import HeroSection from './landing/HeroSection'
import FeaturesSection from './landing/FeaturesSection'
import ToolsSection from './landing/ToolsSection'
import Footer from './landing/Footer'

const LandingPageNew = ({ onCreateSession }) => {
  return (
    <div 
      style={{
        background: 'linear-gradient(180deg, #0A0E17 0%, #050810 100%)',
        minHeight: '100vh',
        width: '100vw',
        position: 'relative'
      }}
    >
      {/* Simple Background */}
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: -1,
          backgroundImage: `
            radial-gradient(circle at 20% 30%, rgba(0, 217, 255, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.15) 0%, transparent 50%)
          `
        }}
      />

      {/* Main Content */}
      <div style={{ position: 'relative', zIndex: 10 }}>
        <Navbar onCreateSession={onCreateSession} />
        <HeroSection onCreateSession={onCreateSession} />
        <FeaturesSection />
        <ToolsSection />
        <Footer />
      </div>
    </div>
  )
}

export default LandingPageNew
