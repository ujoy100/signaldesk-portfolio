import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { expect, test } from '@playwright/test'

const frontendDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const repositoryDir = path.dirname(frontendDir)
const screenshotsDir = path.join(repositoryDir, 'docs', 'screenshots')

function acceptanceValue(role, expired = false) {
  const arguments_ = ['compose', 'exec', '-T', 'backend', 'python', '-m', 'backend.scripts.issue_development_token', role]
  if (expired) arguments_.push('--expired')
  return execFileSync('docker', arguments_, {
    cwd: repositoryDir,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  }).trim()
}

async function login(page, token, role) {
  await page.goto('/')
  await page.getByLabel('Access token').fill(token)
  await page.getByRole('button', { name: 'Sign in securely' }).click()
  await expect(page.getByText('Signed in as')).toBeVisible()
  await expect(page.locator('.identity')).toContainText(role.replace('_', ' '))
}

test.describe.serial('Phase 15 real-browser acceptance', () => {
  let agentToken
  let supervisorToken
  let adminToken
  let ticketId

  test.beforeAll(() => {
    agentToken = acceptanceValue('support_agent')
    supervisorToken = acceptanceValue('supervisor')
    adminToken = acceptanceValue('admin')
    ticketId = acceptanceValue('ticket_id')
  })

  test('loads React, rejects invalid and expired sessions, and handles transport errors safely', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Telecom support, grounded and controlled.' })).toBeVisible()
    await page.getByLabel('Access token').fill('not-a-token')
    await page.getByRole('button', { name: 'Sign in securely' }).click()
    await expect(page.getByRole('alert')).toContainText('Invalid authentication token')

    await page.getByLabel('Access token').fill(acceptanceValue('support_agent', true))
    await page.getByRole('button', { name: 'Sign in securely' }).click()
    await expect(page.getByRole('alert')).toContainText('Invalid authentication token')

    await page.route('**/api/v1/session', (route) => route.abort())
    await page.getByLabel('Access token').fill('fictional-unavailable-backend-token')
    await page.getByRole('button', { name: 'Sign in securely' }).click()
    await expect(page.getByRole('alert')).toHaveText('Backend unavailable')
  })

  test('uses role-aware deterministic support, renders citations, and records feedback', async ({ page }) => {
    await login(page, agentToken, 'support_agent')
    await expect(page.getByRole('navigation')).toContainText('support')
    await expect(page.getByRole('navigation')).toContainText('feedback')
    await expect(page.getByRole('navigation')).not.toContainText('approvals')
    await expect(page.getByRole('navigation')).not.toContainText('knowledge')

    await page.getByLabel('Customer issue').fill('How do I activate my fictional SIM?')
    const responsePromise = page.waitForResponse((response) => response.url().endsWith('/api/v1/support/issues') && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Start investigation' }).click()
    expect((await (await responsePromise).json()).thread_id).toBeTruthy()
    await expect(page.getByText('Deterministic LangGraph', { exact: true })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Evidence & citations' })).toBeVisible()
    await expect(page.locator('.evidence').first()).toBeVisible()
    await page.screenshot({ path: path.join(screenshotsDir, 'phase15-support.png'), fullPage: true })

    await page.getByRole('button', { name: 'feedback', exact: true }).click()
    await expect(page.getByText('Your feedback is linked automatically to this resolution.')).toBeVisible()
    await page.getByLabel('Comment').fill('Fictional browser acceptance feedback.')
    await page.getByRole('button', { name: 'Submit feedback' }).click()
    await expect(page.getByRole('status')).toHaveText('Feedback recorded.')
    await page.screenshot({ path: path.join(screenshotsDir, 'phase15-feedback.png'), fullPage: true })
  })

  test('edits an approval and requires a replacement authorization', async ({ page, request }) => {
    const proposal = await request.post('http://127.0.0.1:8000/api/v1/support/issues', {
      headers: { Authorization: `Bearer ${agentToken}` },
      data: {
        issue: 'Apply the cited SIM activation guidance and resolve this fictional ticket',
        ticket_id: Number(ticketId),
        propose_ticket_update: true,
      },
    })
    expect(proposal.ok()).toBeTruthy()
    const proposed = await proposal.json()
    expect(proposed.status).toBe('approval_pending')

    await login(page, supervisorToken, 'supervisor')
    await expect(page.getByRole('navigation')).toContainText('approvals')
    await expect(page.getByRole('navigation')).not.toContainText('knowledge')
    await page.getByRole('button', { name: 'approvals' }).click()
    const original = page.locator('.record').filter({ hasText: `#${proposed.approval_id} · Update` })
    await expect(original).toBeVisible()
    await expect(original).toContainText('Current status')
    await original.getByRole('button', { name: 'Edit proposed values' }).click()
    await original.getByLabel('Proposed status').selectOption('in_progress')
    await original.getByLabel('Proposed priority').selectOption('high')
    const editResponsePromise = page.waitForResponse((response) => response.url().includes(`/api/v1/approvals/${proposed.approval_id}/decisions`) && response.request().method() === 'POST')
    await original.getByRole('button', { name: 'Submit edit for reauthorization' }).click()
    const replacementId = (await (await editResponsePromise).json()).approval_id
    await expect(original.locator('.status')).toHaveText('rejected')

    const replacement = page.locator('.record').filter({ hasText: `#${replacementId} · Update` })
    await expect(replacement).toBeVisible()
    await replacement.getByRole('button', { name: 'Approve' }).click()
    await expect(page.locator('.record').filter({ hasText: `#${replacementId} · Update` }).locator('.status')).toHaveText('executed')
    await page.screenshot({ path: path.join(screenshotsDir, 'phase15-approval.png'), fullPage: true })
  })

  test('uses admin knowledge-promotion controls and displays feedback history', async ({ page, request }) => {
    const suffix = Date.now().toString(36)
    const upload = await request.post('http://127.0.0.1:8000/api/v1/knowledge/versions', {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: {
        version: '1.0',
        media_type: 'text/markdown',
        content: 'Fictional browser acceptance policy for safe SIM activation verification.',
        metadata: {
          document_id: `browser-policy-${suffix}`,
          source: `fictional://browser/${suffix}`,
          service: 'mobile', category: 'activation', version: '1.0', active: false,
          access_roles: ['public'], page: 1, section: 'Acceptance', title: 'Browser acceptance policy',
        },
      },
    })
    expect(upload.ok()).toBeTruthy()
    const version = await upload.json()

    await login(page, adminToken, 'admin')
    await expect(page.getByRole('navigation')).toContainText('knowledge')
    await page.getByRole('button', { name: 'knowledge' }).click()
    const draft = page.locator('.record').filter({ hasText: `#${version.version_id} · Document` })
    await expect(draft).toBeVisible()
    const requestResponsePromise = page.waitForResponse((response) => response.url().includes(`/api/v1/knowledge/versions/${version.version_id}/promotion-requests`) && response.request().method() === 'POST')
    await draft.getByRole('button', { name: 'Request promotion' }).click()
    const promotionApprovalId = (await (await requestResponsePromise).json()).approval_id

    await page.getByRole('button', { name: 'approvals' }).click()
    const pending = page.locator('.record').filter({ hasText: `#${promotionApprovalId} · Promote Knowledge` })
    await expect(pending).toBeVisible()
    await pending.getByRole('button', { name: 'Approve' }).click()
    const approved = page.locator('.record').filter({ hasText: `#${promotionApprovalId} · Promote Knowledge` })
    await approved.getByRole('button', { name: 'Execute approved promotion' }).click()
    await expect(approved.locator('.status')).toHaveText('executed')
    await page.getByRole('button', { name: 'knowledge' }).click()
    await expect(page.getByRole('heading', { name: 'Knowledge lifecycle' })).toBeVisible()
    await expect(page.locator('.record').filter({ hasText: `#${version.version_id} · Document` })).toBeVisible()
    await page.screenshot({ path: path.join(screenshotsDir, 'phase15-knowledge.png'), fullPage: true })

    await page.getByRole('button', { name: 'feedback', exact: true }).click()
    await expect(page.getByText('Fictional browser acceptance feedback.').first()).toBeVisible()
  })

  test('keeps credentials out of browser storage and remains usable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await login(page, agentToken, 'support_agent')
    await expect(page.getByRole('navigation')).toBeVisible()
    await expect(page.getByLabel('Customer issue')).toBeVisible()
    expect(await page.evaluate(() => ({ local: { ...localStorage }, session: { ...sessionStorage } }))).toEqual({ local: {}, session: {} })
    await page.screenshot({ path: path.join(screenshotsDir, 'phase15-mobile.png'), fullPage: true })
  })
})
