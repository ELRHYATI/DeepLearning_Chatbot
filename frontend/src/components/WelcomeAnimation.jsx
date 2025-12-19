import { useEffect, useState } from 'react'
import { Sparkles, BookOpen, Brain, Zap, MessageSquare } from 'lucide-react'

const WelcomeAnimation = ({ onComplete }) => {
  const [phase, setPhase] = useState(0) // 0: particles, 1: text, 2: icons
  const [particles, setParticles] = useState([])

  useEffect(() => {
    // Créer des particules animées avec plus de variété
    const newParticles = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 2,
      duration: 3 + Math.random() * 2,
      size: 2 + Math.random() * 3,
      opacity: 0.3 + Math.random() * 0.4
    }))
    setParticles(newParticles)

    // Séquence d'animation d'entrée (sans fade out)
    const timers = [
      setTimeout(() => setPhase(1), 600), // Afficher le texte après 600ms
      setTimeout(() => setPhase(2), 1500) // Afficher les icônes après 1500ms
    ]

    return () => timers.forEach(timer => clearTimeout(timer))
  }, [])

  const messages = [
    "✨ Bienvenue dans votre assistant académique",
    "🚀 Prêt à explorer et apprendre",
    "💬 Commençons votre conversation"
  ]

  const features = [
    { icon: Brain, text: "IA Avancée", color: "text-purple-500" },
    { icon: BookOpen, text: "Ressources", color: "text-blue-500" },
    { icon: Zap, text: "Rapide", color: "text-yellow-500" },
    { icon: MessageSquare, text: "Conversation", color: "text-green-500" }
  ]

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 overflow-hidden animate-gradient-shift">
      {/* Gradient animé en arrière-plan */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-100/50 via-purple-100/30 to-pink-100/50 dark:from-primary-900/20 dark:via-purple-900/10 dark:to-pink-900/20 animate-gradient-flow" />
      
      {/* Particules animées en arrière-plan */}
      <div className="absolute inset-0">
        {particles.map((particle) => (
          <div
            key={particle.id}
            className="absolute rounded-full bg-primary-400 dark:bg-primary-500"
            style={{
              left: `${particle.x}%`,
              top: `${particle.y}%`,
              width: `${particle.size}px`,
              height: `${particle.size}px`,
              opacity: particle.opacity,
              animation: `floatSmooth ${particle.duration}s ease-in-out ${particle.delay}s infinite`,
              animationDirection: particle.id % 2 === 0 ? 'alternate' : 'alternate-reverse'
            }}
          />
        ))}
      </div>

      {/* Contenu principal */}
      <div className="relative z-10 text-center px-4">
        {/* Logo/Icone principale avec animation infinie */}
        <div className="mb-8 flex justify-center">
          <div className={`
            relative transition-all duration-1000 ease-out
            ${phase >= 1 ? 'scale-100 opacity-100' : 'scale-0 opacity-0'}
          `}>
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-2xl animate-gradient-rotate">
              <Sparkles className="w-12 h-12 text-white" />
            </div>
            {/* Cercles concentriques animés en boucle */}
            <div className="absolute inset-0 rounded-full border-4 border-primary-300 dark:border-primary-600 animate-ripple opacity-30" />
            <div className="absolute inset-0 rounded-full border-4 border-purple-300 dark:border-purple-600 animate-ripple opacity-30" style={{ animationDelay: '1s' }} />
            <div className="absolute inset-0 rounded-full border-4 border-pink-300 dark:border-pink-600 animate-ripple opacity-30" style={{ animationDelay: '2s' }} />
          </div>
        </div>

        {/* Messages de bienvenue avec animation fluide */}
        <div className="space-y-4 mb-12">
          {messages.map((message, index) => (
            <h1
              key={index}
              className={`
                text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 
                bg-clip-text text-transparent animate-gradient-text
                transition-all duration-1000 ease-out
                ${phase >= 1 
                  ? 'opacity-100 translate-y-0' 
                  : 'opacity-0 translate-y-4'
                }
              `}
              style={{
                animationDelay: `${index * 250}ms`,
                animation: phase >= 1 ? 'fadeInUpSmooth 1s ease-out forwards' : 'none'
              }}
            >
              {phase >= 1 ? message : ''}
            </h1>
          ))}
        </div>

        {/* Icônes de fonctionnalités avec animation infinie */}
        {phase >= 2 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-2xl mx-auto">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <div
                  key={index}
                  className={`
                    flex flex-col items-center gap-2 p-4 rounded-xl
                    bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm
                    border border-gray-200 dark:border-gray-700
                    transition-all duration-700 ease-out hover:scale-110 hover:shadow-lg
                    animate-float-gentle
                    ${phase >= 2 
                      ? 'opacity-100 translate-y-0' 
                      : 'opacity-0 translate-y-8'
                    }
                  `}
                  style={{
                    animationDelay: `${index * 150}ms`,
                    animation: phase >= 2 ? 'bounceInSmooth 0.8s ease-out forwards' : 'none',
                    animationFillMode: 'both'
                  }}
                >
                  <Icon 
                    className={`w-8 h-8 ${feature.color} animate-float-icon`} 
                    style={{ 
                      animationDelay: `${index * 200}ms`,
                      animationDuration: '3s'
                    }} 
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {feature.text}
                  </span>
                </div>
              )
            })}
          </div>
        )}

        {/* Indicateur de chargement subtil en boucle */}
        {phase >= 2 && (
          <div className="mt-12 flex justify-center gap-2">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-primary-500 animate-pulse-smooth"
                style={{
                  animationDelay: `${i * 0.3}s`,
                  animationDuration: '1.5s'
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Styles d'animation inline */}
      <style>{`
        @keyframes floatSmooth {
          0%, 100% {
            transform: translateY(0) translateX(0) scale(1);
            opacity: 0.6;
          }
          25% {
            transform: translateY(-15px) translateX(5px) scale(1.1);
            opacity: 0.8;
          }
          50% {
            transform: translateY(-25px) translateX(10px) scale(1);
            opacity: 1;
          }
          75% {
            transform: translateY(-15px) translateX(5px) scale(0.9);
            opacity: 0.8;
          }
        }
        
        @keyframes fadeInUpSmooth {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes bounceInSmooth {
          0% {
            opacity: 0;
            transform: translateY(30px) scale(0.7);
          }
          50% {
            transform: translateY(-8px) scale(1.08);
          }
          70% {
            transform: translateY(2px) scale(0.95);
          }
          100% {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        
        @keyframes floatGentle {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-10px);
          }
        }
        
        @keyframes floatIcon {
          0%, 100% {
            transform: translateY(0);
          }
          25% {
            transform: translateY(-8px);
          }
          50% {
            transform: translateY(-12px);
          }
          75% {
            transform: translateY(-8px);
          }
        }
        
        @keyframes gradientText {
          0%, 100% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
        }
        
        @keyframes gradientRotate {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }
        
        @keyframes gradientFlow {
          0%, 100% {
            opacity: 0.5;
            transform: scale(1);
          }
          50% {
            opacity: 0.8;
            transform: scale(1.1);
          }
        }
        
        @keyframes ripple {
          0% {
            transform: scale(1);
            opacity: 0.3;
          }
          50% {
            transform: scale(1.5);
            opacity: 0.1;
          }
          100% {
            transform: scale(2);
            opacity: 0;
          }
        }
        
        @keyframes pulseSmooth {
          0%, 100% {
            opacity: 0.4;
            transform: scale(1);
          }
          50% {
            opacity: 1;
            transform: scale(1.2);
          }
        }
        
        .animate-gradient-text {
          background-size: 200% auto;
          animation: gradientText 3s ease infinite;
        }
        
        .animate-gradient-rotate {
          background-size: 200% 200%;
          animation: gradientRotate 4s ease infinite;
        }
        
        .animate-gradient-flow {
          animation: gradientFlow 8s ease-in-out infinite;
        }
        
        .animate-gradient-shift {
          animation: gradientFlow 10s ease-in-out infinite;
        }
        
        .animate-float-gentle {
          animation: floatGentle 4s ease-in-out infinite;
        }
        
        .animate-float-icon {
          animation: floatIcon 3s ease-in-out infinite;
        }
        
        .animate-ripple {
          animation: ripple 3s ease-out infinite;
        }
        
        .animate-pulse-smooth {
          animation: pulseSmooth 1.5s ease-in-out infinite;
        }
      `}</style>
    </div>
  )
}

export default WelcomeAnimation

