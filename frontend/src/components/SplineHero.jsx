import { Suspense, lazy, useState } from 'react'
import { motion } from 'framer-motion'

const Spline = lazy(() => import('@splinetool/react-spline'))

// A public Spline community scene. If it ever fails to load (offline / removed),
// we gracefully fall back to an animated CSS orb so the page still looks alive.
const SCENE_URL = 'https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode'

function Fallback() {
  return (
    <div className="relative h-full w-full grid place-items-center overflow-hidden">
      <motion.div
        className="h-64 w-64 rounded-full"
        style={{
          background:
            'radial-gradient(circle at 30% 30%, #ffd27a, #ff7a59 40%, #4f8cff 100%)',
          filter: 'blur(2px)',
        }}
        animate={{ scale: [1, 1.08, 1], rotate: [0, 8, 0] }}
        transition={{ repeat: Infinity, duration: 8, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute h-72 w-72 rounded-full border border-white/10"
        animate={{ scale: [1, 1.15, 1], opacity: [0.5, 0.1, 0.5] }}
        transition={{ repeat: Infinity, duration: 5, ease: 'easeInOut' }}
      />
    </div>
  )
}

export default function SplineHero() {
  const [failed, setFailed] = useState(false)
  if (failed) return <Fallback />
  return (
    <Suspense fallback={<Fallback />}>
      <div className="h-full w-full overflow-hidden">
        <Spline scene={SCENE_URL} onError={() => setFailed(true)} />
      </div>
    </Suspense>
  )
}
