import { useEffect } from 'react'
import { useAppState } from './storage/hooks'
import { navigate, syncHashRoute } from './storage/store'
import { ArchiveScreen } from './screens/ArchiveScreen'
import { HomeScreen } from './screens/HomeScreen'
import { NewRoundScreen } from './screens/NewRoundScreen'
import { ScorecardScreen } from './screens/ScorecardScreen'
import { ScoreScreen } from './screens/ScoreScreen'

export default function App() {
  const state = useAppState()
  const active = state.rounds.find((r) => r.id === state.activeRoundId)

  useEffect(() => {
    syncHashRoute()
    const onHash = () => syncHashRoute()
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  useEffect(() => {
    if (
      (state.screen === 'score' || state.screen === 'scorecard') &&
      !active
    ) {
      navigate('home')
    }
  }, [state.screen, active])

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
