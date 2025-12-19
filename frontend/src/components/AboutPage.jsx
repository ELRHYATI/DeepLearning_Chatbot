import { motion } from 'framer-motion'
import { 
  Sparkles, Code, Brain, Zap, Shield, Globe, 
  ArrowLeft, Database,
  Cpu, Layers, GitBranch, Server, Lock, Users,
  BookOpen, Lightbulb, Target, Rocket, FileCode
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useTheme } from '../contexts/ThemeContext'

const AboutPage = () => {
  const navigate = useNavigate()
  const { isDark } = useTheme()

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Intelligence",
      description: "Advanced machine learning models for natural language understanding and generation",
      color: "from-cyan-500 to-blue-500"
    },
    {
      icon: BookOpen,
      title: "Grammar Correction",
      description: "Real-time grammar and syntax checking with intelligent suggestions",
      color: "from-purple-500 to-pink-500"
    },
    {
      icon: Lightbulb,
      title: "Q&A System",
      description: "Get instant answers to your academic questions with detailed explanations",
      color: "from-yellow-500 to-orange-500"
    },
    {
      icon: Zap,
      title: "Text Reformulation",
      description: "Rephrase and improve your writing while maintaining your original meaning",
      color: "from-green-500 to-emerald-500"
    }
  ]

  const techStack = [
    { name: "React", icon: Code, color: "text-cyan-400", bg: "bg-cyan-500/10" },
    { name: "Python", icon: FileCode, color: "text-blue-400", bg: "bg-blue-500/10" },
    { name: "AI/ML", icon: Brain, color: "text-purple-400", bg: "bg-purple-500/10" },
    { name: "Node.js", icon: Server, color: "text-green-400", bg: "bg-green-500/10" },
    { name: "Database", icon: Database, color: "text-yellow-400", bg: "bg-yellow-500/10" },
    { name: "API", icon: GitBranch, color: "text-pink-400", bg: "bg-pink-500/10" }
  ]

  const howItWorks = [
    {
      step: 1,
      title: "Input Your Text",
      description: "Enter your text, question, or document that needs assistance",
      icon: BookOpen
    },
    {
      step: 2,
      title: "AI Processing",
      description: "Our advanced AI analyzes your content using NLP and ML models",
      icon: Cpu
    },
    {
      step: 3,
      title: "Get Results",
      description: "Receive intelligent suggestions, corrections, or answers instantly",
      icon: Sparkles
    },
    {
      step: 4,
      title: "Refine & Improve",
      description: "Iterate and improve your work with continuous AI assistance",
      icon: Target
    }
  ]

  return (
    <div 
      className="min-h-screen w-full relative overflow-hidden"
      style={{ background: isDark ? '#0F1419' : '#F8FAFC' }}
    >
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl"></div>
      </div>

      {/* Header */}
      <div className="relative z-10 border-b" style={{ borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)' }}>
        <div className="max-w-7xl mx-auto px-6 py-4">
          <motion.button
            onClick={() => navigate(-1)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              isDark 
                ? 'text-white/70 hover:text-white hover:bg-white/5' 
                : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
            }`}
            whileHover={{ x: -3 }}
            whileTap={{ scale: 0.95 }}
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back</span>
          </motion.button>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-12">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center shadow-lg ${
              isDark ? 'shadow-cyan-500/30' : 'shadow-purple-500/20'
            }`}>
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h1 className={`text-5xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              À propos
            </h1>
          </div>
          <p className={`text-xl max-w-2xl mx-auto ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
            Academic AI - Your intelligent academic assistant powered by advanced AI and machine learning
          </p>
        </motion.div>

        {/* About Us Section */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-16"
        >
          <div className={`p-8 rounded-3xl border ${
            isDark 
              ? 'bg-[#1A1F2E] border-white/10' 
              : 'bg-white border-gray-200'
          }`}
          style={{
            boxShadow: isDark 
              ? '0 10px 40px rgba(0, 217, 255, 0.1), 0 0 20px rgba(99, 102, 241, 0.1)' 
              : '0 10px 40px rgba(0, 0, 0, 0.05)'
          }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center ${
                isDark ? 'shadow-lg shadow-cyan-500/30' : 'shadow-md'
              }`}>
                <Users className="w-6 h-6 text-white" />
              </div>
              <h2 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                About Us
              </h2>
            </div>
            <div className="space-y-4">
              <p className={`text-lg leading-relaxed ${isDark ? 'text-white/80' : 'text-gray-700'}`}>
                Academic AI is an intelligent assistant designed to help students, researchers, and academics 
                enhance their writing and research capabilities. We leverage cutting-edge artificial intelligence 
                and machine learning technologies to provide real-time grammar correction, intelligent Q&A, 
                and advanced text reformulation.
              </p>
              <p className={`text-lg leading-relaxed ${isDark ? 'text-white/80' : 'text-gray-700'}`}>
                Our mission is to make academic writing more accessible, efficient, and error-free, allowing 
                users to focus on their ideas while our AI handles the technical aspects of language and communication.
              </p>
            </div>
          </div>
        </motion.section>

        {/* Features Grid */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mb-16"
        >
          <h2 className={`text-3xl font-bold text-center mb-12 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Our Features
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.4 + index * 0.1 }}
                  className={`p-6 rounded-2xl border ${
                    isDark 
                      ? 'bg-[#1E2433] border-white/10 hover:border-cyan-500/30' 
                      : 'bg-white border-gray-200 hover:border-purple-300'
                  } transition-all group`}
                  style={{
                    boxShadow: isDark 
                      ? '0 4px 20px rgba(0, 0, 0, 0.3)' 
                      : '0 4px 20px rgba(0, 0, 0, 0.05)'
                  }}
                  whileHover={{ y: -5, scale: 1.02 }}
                >
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 shadow-lg`}>
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  <h3 className={`text-xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    {feature.title}
                  </h3>
                  <p className={`text-sm leading-relaxed ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                    {feature.description}
                  </p>
                </motion.div>
              )
            })}
          </div>
        </motion.section>

        {/* How It Works */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mb-16"
        >
          <div className={`p-8 rounded-3xl border ${
            isDark 
              ? 'bg-[#1A1F2E] border-white/10' 
              : 'bg-white border-gray-200'
          }`}
          style={{
            boxShadow: isDark 
              ? '0 10px 40px rgba(99, 102, 241, 0.1), 0 0 20px rgba(0, 217, 255, 0.1)' 
              : '0 10px 40px rgba(0, 0, 0, 0.05)'
          }}
          >
            <div className="flex items-center gap-3 mb-8">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center ${
                isDark ? 'shadow-lg shadow-purple-500/30' : 'shadow-md'
              }`}>
                <Rocket className="w-6 h-6 text-white" />
              </div>
              <h2 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                How It Works
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {howItWorks.map((item, index) => {
                const Icon = item.icon
                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.6 + index * 0.1 }}
                    className="relative"
                  >
                    <div className={`p-6 rounded-2xl border ${
                      isDark 
                        ? 'bg-[#1E2433] border-white/10' 
                        : 'bg-gray-50 border-gray-200'
                    } h-full`}>
                      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center mb-4 shadow-lg`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      <div className={`w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm mb-3 ${
                        isDark ? 'shadow-lg shadow-cyan-500/30' : 'shadow-md'
                      }`}>
                        {item.step}
                      </div>
                      <h3 className={`text-lg font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        {item.title}
                      </h3>
                      <p className={`text-sm leading-relaxed ${isDark ? 'text-white/70' : 'text-gray-600'}`}>
                        {item.description}
                      </p>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </div>
        </motion.section>

        {/* Tech Stack */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mb-16"
        >
          <div className={`p-8 rounded-3xl border ${
            isDark 
              ? 'bg-[#1A1F2E] border-white/10' 
              : 'bg-white border-gray-200'
          }`}
          style={{
            boxShadow: isDark 
              ? '0 10px 40px rgba(0, 217, 255, 0.1), 0 0 20px rgba(99, 102, 241, 0.1)' 
              : '0 10px 40px rgba(0, 0, 0, 0.05)'
          }}
          >
            <div className="flex items-center gap-3 mb-8">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center ${
                isDark ? 'shadow-lg shadow-green-500/30' : 'shadow-md'
              }`}>
                <Code className="w-6 h-6 text-white" />
              </div>
              <h2 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Technology Stack
              </h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {techStack.map((tech, index) => {
                const Icon = tech.icon
                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, delay: 0.8 + index * 0.05 }}
                    className={`p-4 rounded-xl border ${
                      isDark 
                        ? 'bg-[#1E2433] border-white/10 hover:border-cyan-500/30' 
                        : 'bg-gray-50 border-gray-200 hover:border-purple-300'
                    } transition-all text-center group`}
                    whileHover={{ y: -5, scale: 1.05 }}
                  >
                    <div className={`w-12 h-12 rounded-lg ${tech.bg} flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform`}>
                      <Icon className={`w-6 h-6 ${tech.color}`} />
                    </div>
                    <p className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                      {tech.name}
                    </p>
                  </motion.div>
                )
              })}
            </div>
          </div>
        </motion.section>

        {/* Security & Privacy */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.9 }}
          className="mb-16"
        >
          <div className={`p-8 rounded-3xl border ${
            isDark 
              ? 'bg-[#1A1F2E] border-white/10' 
              : 'bg-white border-gray-200'
          }`}
          style={{
            boxShadow: isDark 
              ? '0 10px 40px rgba(0, 217, 255, 0.1), 0 0 20px rgba(99, 102, 241, 0.1)' 
              : '0 10px 40px rgba(0, 0, 0, 0.05)'
          }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-teal-500 flex items-center justify-center ${
                isDark ? 'shadow-lg shadow-green-500/30' : 'shadow-md'
              }`}>
                <Shield className="w-6 h-6 text-white" />
              </div>
              <h2 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Security & Privacy
              </h2>
            </div>
            <p className={`text-lg leading-relaxed ${isDark ? 'text-white/80' : 'text-gray-700'}`}>
              We take your privacy and data security seriously. All communications are encrypted, and your 
              data is processed securely. We use industry-standard security practices to protect your information 
              and ensure your academic work remains confidential.
            </p>
          </div>
        </motion.section>

        {/* Footer with Copyright */}
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1 }}
          className={`text-center py-8 border-t ${
            isDark ? 'border-white/10' : 'border-gray-200'
          }`}
        >
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center ${
              isDark ? 'shadow-lg shadow-cyan-500/30' : 'shadow-md'
            }`}>
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Academic AI
            </span>
          </div>
          <p className={`text-sm ${isDark ? 'text-white/60' : 'text-gray-600'}`}>
            © {new Date().getFullYear()} Academic AI. All rights reserved.
          </p>
          <p className={`text-xs mt-2 ${isDark ? 'text-white/40' : 'text-gray-500'}`}>
            Powered by advanced AI and machine learning technologies
          </p>
        </motion.footer>
      </div>
    </div>
  )
}

export default AboutPage

