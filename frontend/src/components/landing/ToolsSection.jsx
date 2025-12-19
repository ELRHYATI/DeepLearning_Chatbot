import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import { MessageSquare, FileText, Brain, Languages } from 'lucide-react'

const ToolsSection = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1
  })

  // CUSTOMIZE: Update these tools to match your chatbot modules
  const tools = [
    {
      icon: MessageSquare,
      title: 'General Chat',
      description: 'Ask any academic question and get detailed, accurate answers',
      color: 'cyan',
      gradient: 'from-cyan-500 to-blue-500'
    },
    {
      icon: Languages,
      title: 'Grammar Correction',
      description: 'Fix grammar, spelling, and syntax errors in your text',
      color: 'purple',
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      icon: Brain,
      title: 'Q&A Assistant',
      description: 'Get instant answers to complex academic questions',
      color: 'blue',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      icon: FileText,
      title: 'Text Reformulation',
      description: 'Rephrase and improve your writing while maintaining meaning',
      color: 'indigo',
      gradient: 'from-indigo-500 to-purple-500'
    }
  ]

  return (
    <section id="tools" className="relative py-24 px-6 lg:px-12">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            AI Tools for{' '}
            <span className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
              Every Need
            </span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Choose the right tool for your academic task
          </p>
        </motion.div>

        {/* Tools Grid */}
        <div ref={ref} className="grid md:grid-cols-2 gap-8">
          {tools.map((tool, index) => {
            const Icon = tool.icon
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 50 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ y: -15, scale: 1.02 }}
                className="group relative p-8 rounded-3xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-white/30 transition-all duration-300 overflow-hidden"
              >
                {/* Animated Gradient Border */}
                <motion.div
                  className={`absolute inset-0 rounded-3xl bg-gradient-to-r ${tool.gradient} opacity-0 group-hover:opacity-20 blur-2xl transition-opacity duration-500`}
                  animate={{
                    backgroundPosition: ['0%', '100%', '0%'],
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: 'linear'
                  }}
                  style={{
                    backgroundSize: '200% auto'
                  }}
                />

                {/* Content */}
                <div className="relative z-10">
                  <motion.div
                    whileHover={{ rotate: [0, -10, 10, -10, 0] }}
                    transition={{ duration: 0.5 }}
                    className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${tool.gradient} flex items-center justify-center mb-6 shadow-lg shadow-${tool.color}-500/50`}
                  >
                    <Icon className="w-8 h-8 text-white" />
                  </motion.div>

                  <h3 className="text-2xl font-bold text-white mb-3">{tool.title}</h3>
                  <p className="text-gray-400 leading-relaxed mb-6">{tool.description}</p>

                  <motion.button
                    whileHover={{ x: 5 }}
                    className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300 font-medium group/btn"
                  >
                    Try Now
                    <motion.svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      animate={{ x: [0, 5, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </motion.svg>
                  </motion.button>
                </div>

                {/* Glow Effect */}
                <div className={`absolute -inset-1 rounded-3xl bg-gradient-to-r ${tool.gradient} opacity-0 group-hover:opacity-30 blur-xl transition-opacity duration-500`} />
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

export default ToolsSection

