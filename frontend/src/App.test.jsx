import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { operationsApi } from './api/client'

vi.mock('./api/client', () => ({ microsoftLoginUrl: '/auth/login', operationsApi: { session: vi.fn(), logout: vi.fn(), submitIssue: vi.fn(), approvals: vi.fn(), decide: vi.fn(), decideKnowledge: vi.fn(), requestPromotion: vi.fn(), promote: vi.fn(), evaluations: vi.fn(), knowledge: vi.fn(), submitFeedback: vi.fn(), feedback: vi.fn() } }))

async function login(role = 'support_agent', displayName = 'Verified Microsoft User') {
  operationsApi.session.mockRejectedValueOnce(new Error('No session')).mockResolvedValueOnce({ actor_id: 7, role, display_name: displayName }); render(<App />)
  await screen.findByLabelText('Access token')
  await userEvent.type(screen.getByLabelText('Access token'), 'signed.jwt')
  await userEvent.click(screen.getByRole('button', { name: /sign in/i }))
  await screen.findByText(displayName)
}

describe('operational application', () => {
  beforeEach(() => vi.clearAllMocks())
  afterEach(() => cleanup())
  it('keeps the token in memory and supports logout', async () => {
    await login(); expect(screen.queryByRole('button', { name: 'approvals' })).toBeNull(); expect(screen.getByText('Verified Microsoft User')).toBeTruthy()
    await userEvent.click(screen.getByRole('button', { name: /log out/i })); expect(screen.getByLabelText('Access token')).toBeTruthy(); expect(screen.queryByText('Verified Microsoft User')).toBeNull()
  })
  it('replaces identity data when a different user signs in', async () => {
    await login('support_agent', 'First Microsoft User'); await userEvent.click(screen.getByRole('button', { name: /log out/i }))
    operationsApi.session.mockResolvedValueOnce({ actor_id: 8, role: 'support_agent', display_name: 'Second Microsoft User' })
    await userEvent.type(screen.getByLabelText('Access token'), 'second.jwt'); await userEvent.click(screen.getByRole('button', { name: /sign in/i }))
    expect(await screen.findByText('Second Microsoft User')).toBeTruthy(); expect(screen.queryByText('First Microsoft User')).toBeNull(); expect(screen.getByText('User #8')).toBeTruthy()
  })
  it('shows authentication failures safely', async () => {
    operationsApi.session.mockRejectedValueOnce(new Error('No session')).mockRejectedValueOnce(new Error('Token expired')); render(<App />)
    await screen.findByLabelText('Access token')
    await userEvent.type(screen.getByLabelText('Access token'), 'expired'); await userEvent.click(screen.getByRole('button', { name: /sign in/i }))
    expect((await screen.findByRole('alert')).textContent).toContain('Token expired')
  })
  it('submits and renders a structured grounded resolution', async () => {
    operationsApi.submitIssue.mockResolvedValue({ thread_id: 'thread-123', status: 'completed', workflow_mode: 'deterministic', approval_id: null, resolution: { issue_type: 'sim_activation', likely_cause: 'Activation is still provisioning.', confidence: .9, next_steps: ['Restart the device'], evidence: [{ source_type: 'knowledge', source_id: 'policy-1', title: 'SIM activation', content: 'Provisioning can take several minutes.', version: '1' }] } })
    await login(); await userEvent.type(screen.getByLabelText('Customer issue'), 'My SIM will not activate'); await userEvent.click(screen.getByRole('button', { name: /start investigation/i }))
    expect(await screen.findByText('Activation is still provisioning.')).toBeTruthy(); expect(screen.getAllByText(/policy-1/).length).toBeGreaterThan(0); expect(screen.getByText('Deterministic LangGraph')).toBeTruthy()
    await userEvent.click(screen.getByRole('button', { name: 'feedback' })); expect(screen.getByText(/linked automatically/)).toBeTruthy()
    await userEvent.click(screen.getByRole('button', { name: 'support' })); expect(screen.getByText('Activation is still provisioning.')).toBeTruthy()
  })
  it('allows supervisors to reject pending approvals', async () => {
    operationsApi.approvals.mockResolvedValue([{ id: 9, thread_id: 'thread-9', status: 'pending', action_type: 'update_ticket', action_payload: { ticket_id: 1 }, consumed: false }]); operationsApi.decide.mockResolvedValue({ status: 'completed' })
    await login('supervisor'); await userEvent.click(screen.getByRole('button', { name: 'approvals' })); expect(await screen.findByText(/Update ticket 1/)).toBeTruthy(); fireEvent.click(screen.getByRole('button', { name: 'Reject' }))
    await waitFor(() => expect(operationsApi.decide).toHaveBeenCalledWith('signed.jwt', 9, expect.objectContaining({ decision: 'reject' })))
  })
  it('edits a ticket action only through reauthorization', async () => {
    operationsApi.approvals.mockResolvedValue([{ id: 10, thread_id: 'thread-10', status: 'pending', action_type: 'update_ticket', action_payload: { ticket_id: 2, status: 'resolved' }, consumed: false }]); operationsApi.decide.mockResolvedValue({ status: 'approval_pending', approval_id: 11 })
    await login('supervisor'); await userEvent.click(screen.getByRole('button', { name: 'approvals' })); await screen.findByText(/Update ticket 2/); await userEvent.click(screen.getByRole('button', { name: 'Edit proposed values' })); await userEvent.click(screen.getByRole('button', { name: /Submit edit/ }))
    await waitFor(() => expect(operationsApi.decide).toHaveBeenCalledWith('signed.jwt', 10, expect.objectContaining({ decision: 'edit', edited_action: { operation: 'update_ticket', payload: { ticket_id: 2, status: 'resolved', priority: 'medium' } } })))
  })
  it('submits feedback without exposing review history to agents', async () => {
    operationsApi.submitFeedback.mockResolvedValue({ id: 1, thread_id: 'thread-123', rating: 5, comment: null })
    operationsApi.submitIssue.mockResolvedValue({ thread_id: 'thread-123', status: 'completed', workflow_mode: 'deterministic', resolution: { issue_type: 'general', likely_cause: 'Grounded answer', confidence: .8, next_steps: ['Use cited guidance'], evidence: [] } })
    await login(); await userEvent.type(screen.getByLabelText('Customer issue'), 'Activation issue'); await userEvent.click(screen.getByRole('button', { name: /start investigation/i })); await userEvent.click(screen.getByRole('button', { name: 'feedback' })); await userEvent.click(screen.getByRole('button', { name: 'Submit feedback' }))
    expect(await screen.findByText('Feedback recorded.')).toBeTruthy(); expect(operationsApi.feedback).not.toHaveBeenCalled()
  })
})
