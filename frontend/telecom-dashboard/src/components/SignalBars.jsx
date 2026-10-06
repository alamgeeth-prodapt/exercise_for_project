import './SignalBars.css'

const HEIGHTS = [7, 12, 17, 22]

/**
 * Telecom signal-strength bars, reused two ways across the app:
 *  - variant="loading": four bars pulse in sequence while data is fetched.
 *  - variant="meter": bars fill in to represent retention strength, i.e.
 *    the inverse of churn risk (4 bars = safest, 1 bar = at risk).
 */
export default function SignalBars({ variant = 'loading', strength = 4, label }) {
  const isMeter = variant === 'meter'
  const tone = isMeter ? (strength >= 3 ? 'good' : strength === 2 ? 'mid' : 'bad') : 'neutral'

  return (
    <span className={`signal signal--${variant} signal--${tone}`} role="img" aria-label={label || 'signal strength'}>
      {HEIGHTS.map((h, i) => (
        <span
          key={h}
          className="signal__bar"
          style={{
            height: h,
            animationDelay: variant === 'loading' ? `${i * 0.12}s` : undefined,
            opacity: isMeter ? (i < strength ? 1 : 0.18) : undefined,
          }}
        />
      ))}
    </span>
  )
}
