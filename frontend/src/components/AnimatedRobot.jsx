import { useState, useEffect, useRef } from 'react'
import { motion, useSpring, useMotionValue } from 'framer-motion'
import Lottie from 'lottie-react'

const AnimatedRobot = () => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const [lottieData, setLottieData] = useState(null)
  const robotRef = useRef(null)
  const containerRef = useRef(null)

  // Motion values for smooth spring animation (mouse tracking)
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  // Spring configuration for smooth mouse following
  const springConfig = { damping: 20, stiffness: 100 }
  const xSpring = useSpring(mouseX, springConfig)
  const ySpring = useSpring(mouseY, springConfig)

  // Track mouse position
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY })
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  // Calculate mouse position relative to screen center and update motion values
  useEffect(() => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect()
      const containerCenterX = rect.left + rect.width / 2
      const containerCenterY = rect.top + rect.height / 2

      // Calculate offset from center (limited to reasonable range)
      const deltaX = (mousePosition.x - containerCenterX) * 0.1 // 10% of distance
      const deltaY = (mousePosition.y - containerCenterY) * 0.1

      // Clamp the values to prevent excessive movement
      const maxOffset = 30
      const clampedX = Math.max(-maxOffset, Math.min(maxOffset, deltaX))
      const clampedY = Math.max(-maxOffset, Math.min(maxOffset, deltaY))

      mouseX.set(clampedX)
      mouseY.set(clampedY)
    }
  }, [mousePosition, mouseX, mouseY])

  // Load Lottie animation
  // To add a Lottie animation:
  // 1. Download a robot animation from https://lottiefiles.com
  // 2. Save it as robot-animation.json in frontend/src/assets/
  // 3. Uncomment the lines below and update the import path
  useEffect(() => {
    // Uncomment these lines when you have the Lottie JSON file:
    // import robotAnimation from '../assets/robot-animation.json'
    // setLottieData(robotAnimation)
    
    // Currently using enhanced placeholder robot
    setLottieData(null)
  }, [])

  return (
    <motion.div
      ref={containerRef}
      className="fixed bottom-8 right-8 pointer-events-none z-10 hidden md:block"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ 
        opacity: 1,
        scale: 1
      }}
      transition={{
        opacity: { duration: 0.8 },
        scale: { duration: 0.8 }
      }}
      style={{
        x: xSpring,
        y: ySpring
      }}
    >
      {/* Floating animation wrapper */}
      <motion.div
        animate={{
          y: [0, -15, 0]
        }}
        transition={{
          y: {
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
          }
        }}
      >
      {lottieData ? (
        // Lottie animation will be displayed here when JSON is provided
        <div className="w-48 h-48">
          <Lottie
            animationData={lottieData}
            loop={true}
            autoplay={true}
            style={{ width: '100%', height: '100%' }}
          />
        </div>
      ) : (
        // Enhanced Placeholder Robot - Professional CSS/SVG Animation
        <motion.div
          ref={robotRef}
          className="relative w-40 h-48"
          animate={{
            // Wave animation - continuous loop
            rotate: [0, 5, -5, 0]
          }}
          transition={{
            rotate: {
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }
          }}
        >
          {/* Robot Head with Antennae */}
          <motion.div
            className="w-28 h-28 bg-white rounded-2xl shadow-2xl mx-auto mb-2 relative"
            style={{
              border: '3px solid #06B6D4',
              boxShadow: '0 10px 40px rgba(0, 0, 0, 0.25), 0 0 30px rgba(6, 182, 212, 0.4), inset 0 0 20px rgba(6, 182, 212, 0.1)'
            }}
            animate={{
              scale: [1, 1.02, 1]
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            {/* Antennae */}
            <div className="absolute -left-3 top-6 w-5 h-8 bg-cyan-400 rounded-full shadow-md"></div>
            <div className="absolute -right-3 top-6 w-5 h-8 bg-cyan-400 rounded-full shadow-md"></div>
            
            {/* Screen Face */}
            <div className="absolute inset-2 bg-gray-900 rounded-xl flex items-center justify-center overflow-hidden">
              {/* Corner brackets */}
              <div className="absolute top-1 left-1 w-3 h-3 border-l-2 border-t-2 border-cyan-400/60"></div>
              <div className="absolute top-1 right-1 w-3 h-3 border-r-2 border-t-2 border-cyan-400/60"></div>
              <div className="absolute bottom-1 left-1 w-3 h-3 border-l-2 border-b-2 border-cyan-400/60"></div>
              <div className="absolute bottom-1 right-1 w-3 h-3 border-r-2 border-b-2 border-cyan-400/60"></div>
              
              {/* Glowing Cyan Eyes with Happy Expression */}
              <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                <motion.path
                  d="M 20 50 Q 35 30, 50 50"
                  stroke="#06B6D4"
                  strokeWidth="5"
                  fill="none"
                  strokeLinecap="round"
                  animate={{
                    d: [
                      "M 20 50 Q 35 30, 50 50",
                      "M 20 50 Q 35 25, 50 50",
                      "M 20 50 Q 35 30, 50 50"
                    ],
                    opacity: [0.8, 1, 0.8]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  style={{
                    filter: 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.9))'
                  }}
                />
                <motion.path
                  d="M 50 50 Q 65 30, 80 50"
                  stroke="#06B6D4"
                  strokeWidth="5"
                  fill="none"
                  strokeLinecap="round"
                  animate={{
                    d: [
                      "M 50 50 Q 65 30, 80 50",
                      "M 50 50 Q 65 25, 80 50",
                      "M 50 50 Q 65 30, 80 50"
                    ],
                    opacity: [0.8, 1, 0.8]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 0.1
                  }}
                  style={{
                    filter: 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.9))'
                  }}
                />
              </svg>
            </div>
          </motion.div>

          {/* Robot Body - Segmented */}
          <div className="relative">
            {/* Upper Body */}
            <motion.div
              className="w-24 h-12 bg-white rounded-lg shadow-lg mx-auto relative"
              animate={{
                y: [0, -2, 0]
              }}
              transition={{
                duration: 2.5,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.2
              }}
              style={{
                boxShadow: '0 5px 20px rgba(0, 0, 0, 0.15)'
              }}
            />
            
            {/* Mid-section with glowing circle */}
            <motion.div
              className="w-28 h-8 bg-cyan-400 rounded-lg shadow-lg mx-auto relative"
              animate={{
                y: [0, -1, 0],
                boxShadow: [
                  '0 0 20px rgba(6, 182, 212, 0.6)',
                  '0 0 35px rgba(6, 182, 212, 0.9)',
                  '0 0 20px rgba(6, 182, 212, 0.6)'
                ]
              }}
              transition={{
                y: {
                  duration: 2.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: 0.3
                },
                boxShadow: {
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }
              }}
            >
              <motion.div
                className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-5 h-5 bg-cyan-300 rounded-full"
                animate={{
                  scale: [1, 1.4, 1],
                  opacity: [0.8, 1, 0.8]
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                style={{
                  boxShadow: '0 0 20px rgba(6, 182, 212, 1)'
                }}
              />
            </motion.div>

            {/* Lower Body - Bell-shaped */}
            <motion.div
              className="w-32 h-18 bg-white rounded-t-lg rounded-b-3xl shadow-lg mx-auto relative"
              animate={{
                y: [0, -1, 0]
              }}
              transition={{
                duration: 2.5,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.4
              }}
              style={{
                boxShadow: '0 5px 25px rgba(0, 0, 0, 0.15)'
              }}
            />
          </div>

          {/* Left Arm - Waving */}
          <motion.div
            className="absolute top-10 -left-3"
            animate={{
              rotate: [0, 25, -15, 0],
              y: [0, -8, 0]
            }}
            transition={{
              rotate: {
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              },
              y: {
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }
            }}
            style={{
              transformOrigin: 'top center'
            }}
          >
            {/* Upper arm */}
            <div className="w-4 h-12 bg-white rounded-full shadow-md"></div>
            {/* Forearm/Hand */}
            <div className="w-4 h-10 bg-cyan-400 rounded-full shadow-md -mt-1"></div>
          </motion.div>

          {/* Right Arm */}
          <motion.div
            className="absolute top-14 -right-3"
            animate={{
              rotate: [0, -8, 8, 0],
              y: [0, 3, 0]
            }}
            transition={{
              rotate: {
                duration: 2.5,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.5
              },
              y: {
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.3
              }
            }}
            style={{
              transformOrigin: 'top center'
            }}
          >
            {/* Upper arm */}
            <div className="w-4 h-12 bg-white rounded-full shadow-md"></div>
            {/* Forearm/Hand */}
            <div className="w-4 h-10 bg-cyan-400 rounded-full shadow-md -mt-1"></div>
          </motion.div>

          {/* Legs */}
          <motion.div
            className="absolute bottom-0 left-8"
            animate={{
              y: [0, 3, 0]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.1
            }}
          >
            <div className="w-6 h-8 bg-white rounded-full shadow-md"></div>
            <div className="w-6 h-10 bg-cyan-400 rounded-full shadow-md -mt-1"></div>
          </motion.div>
          
          <motion.div
            className="absolute bottom-0 right-8"
            animate={{
              y: [0, 3, 0]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.3
            }}
          >
            <div className="w-6 h-8 bg-white rounded-full shadow-md"></div>
            <div className="w-6 h-10 bg-cyan-400 rounded-full shadow-md -mt-1"></div>
          </motion.div>
        </motion.div>
      )}
      </motion.div>
    </motion.div>
  )
}

export default AnimatedRobot
