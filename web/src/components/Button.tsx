import type { MouseEventHandler, ReactNode } from 'react'
import { cn } from '../lib/cn'

const variants = {
  primary: 'bg-elevated text-fg border border-line active:bg-line',
  secondary: 'bg-card text-fg border border-line active:bg-elevated',
  ghost: 'bg-transparent text-fg active:bg-elevated',
  danger:
    'bg-danger text-danger-ink border border-danger-line active:brightness-95',
  outline: 'bg-card text-fg border-2 border-line active:bg-elevated',
  lime: 'bg-accent text-accent-ink border border-accent active:brightness-95',
} as const

const sizes = {
  md: 'min-h-12 px-4 text-base',
  lg: 'min-h-14 px-5 text-lg',
  xl: 'min-h-16 px-6 text-xl font-semibold',
  icon: 'size-14 text-2xl',
} as const

type ButtonProps = {
  className?: string
  variant?: keyof typeof variants
  size?: keyof typeof sizes
  type?: 'button' | 'submit' | 'reset'
  children?: ReactNode
  disabled?: boolean
  onClick?: MouseEventHandler<HTMLButtonElement>
  'aria-label'?: string
}

export function Button({
  className,
  variant = 'primary',
  size = 'lg',
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-2xl font-medium select-none',
        'disabled:opacity-40 disabled:pointer-events-none',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  )
}
