import { useEffect, useState } from 'react'
import { useAppState } from './storage/hooks'
import { bootStore, navigate, syncHashRoute } from './storage/store'
import { ArchiveScreen } from './screens/ArchiveScreen'
import { HomeScreen } from './screens/HomeScreen'
import { NewRoundScreen } from './screens/NewRoundScreen'
import { ScorecardScreen } from './screens/ScorecardScreen'
import { ScoreScreen } from './screens/ScoreScreen'

export default function App() {
  const [ready, setReady] = useState(false)
  const state = useAppState()
  const active = state.rounds.find((r) => r.id === state.activeRoundId)

  useEffect(() => {
    let cancelled = false
    void bootStore().then(() => {
      if (!cancelled) setReady(true)
    })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!ready) return
    syncHashRoute()
    const onHash = () => syncHashRoute()
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [ready])

  useEffect(() => {
    if (!ready) return
    if (
      (state.screen === 'score' || state.screen === 'scorecard') &&
      !active
    ) {
      navigate('home')
    }
  }, [ready, state.screen, active])

  if (!ready) {
    return (
      <div className="flex min-h-dvh items-center justify-center px-4 text-muted">
        載入成績庫…
      </div>
    )
  }

  if (state.screen === 'new') return <NewRoundScreen />
  if (state.screen === 'archive') return <ArchiveScreen />
  if (state.screen === 'score' && active) {
    return <ScoreScreen state={state} round={active} />
  }
  if (state.screen === 'scorecard' && active) {
    return <ScorecardScreen round={active} />
  }
  return <HomeScreen rounds={state.rounds} />
}
