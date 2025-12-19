import { Suspense, lazy } from 'react'

// Lazy load Spline with error handling
const Spline = lazy(() => 
  import('@splinetool/react-spline').catch(() => ({
    default: () => null
  }))
)

const SplineRobot = () => {
  // CUSTOMIZE: Replace this URL with your Spline scene URL
  // 
  // QUICK GUIDE:
  // 1. Go to https://spline.design and sign up (free)
  // 2. Click "New File" → Browse templates → Search "robot"
  // 3. Select a robot template and customize if needed
  // 4. Click "Publish" button (top right) → "Export as URL"
  // 5. Copy the URL and paste it below
  // 
  // Alternative: Use a free model from Sketchfab, upload to Spline, then publish
  // 
  // For detailed instructions, see: frontend/src/components/landing/SPLINE_ROBOT_GUIDE.md
  const splineUrl = 'https://prod.spline.design/YOUR_SCENE_URL_HERE.scene'

  return (
    <div className="w-full h-full relative">
      <Suspense fallback={
        <div className="w-full h-full flex items-center justify-center">
          <div className="w-32 h-32 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
        </div>
      }>
        {/* CUSTOMIZE: Add your Spline scene URL */}
        {/* For now, showing a placeholder until you add your Spline URL */}
        {splineUrl.includes('YOUR_SCENE_URL') ? (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-cyan-500/10 to-purple-500/10 rounded-3xl border border-white/10">
            <div className="text-center p-8">
              <div className="w-24 h-24 mx-auto mb-4 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-2xl flex items-center justify-center">
                <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <p className="text-white/70 text-sm mb-2">3D Robot Placeholder</p>
              <p className="text-white/50 text-xs">Add your Spline scene URL in SplineRobot.jsx</p>
            </div>
          </div>
        ) : (
          <Spline scene={splineUrl} />
        )}
      </Suspense>
    </div>
  )
}

export default SplineRobot
