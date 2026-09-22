import { useSyncExternalStore } from 'react'
import { getState, subscribe } from '../storage/store'
import type { AppState } from '../types'

export function useAppState(): AppState {
  return useSyncExternalStore(subscribe, getState, getState)
}
