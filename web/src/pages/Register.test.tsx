import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import Register from './Register'

describe('Register', () => {
  it('requires the invite code before enabling submission', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    )

    const submitButton = screen.getByTestId('register-submit')
    expect(submitButton).toBeDisabled()

    await user.type(screen.getByTestId('register-name'), 'Alice')
    await user.type(screen.getByTestId('register-email'), 'alice@example.com')
    await user.type(screen.getByTestId('register-password'), 'password123')

    expect(submitButton).toBeDisabled()

    await user.type(screen.getByTestId('register-invite-code'), 'invite-code')

    expect(submitButton).toBeEnabled()
  })
})