import './DemoBanner.css'

export default function DemoBanner({ onExit }) {
  return (
    <div className="demo-banner">
      <button className="demo-banner__exit" onClick={onExit}>
        ← Exit Demo
      </button>
      <div className="demo-banner__center">
        <h1 className="demo-banner__title">Demo Mode</h1>
        <p className="demo-banner__caption">Runs on synthetically generated data</p>
      </div>
    </div>
  )
}
